from functools import reduce
from datetime import datetime
import pytz
from data import TaskStatus,OutputType,DetailType
import re



timezone = pytz.timezone('Asia/Shanghai')

date_object = datetime.now(timezone)
utc_offset_seconds = date_object.utcoffset().total_seconds()



def refine_prompt(space_name: str, prompt: str):
    pattern = r'(--?\w+\s+[\w:\.]+)+'
    new_prompt = ""
    unique_params = {}
    allowed_keys = set((
        "--aspect", 
        "--ar", 
        "--chaos",
        "--iw",
        "--no",
        "--quality",
        "--q",
        "--repeat",
        "--seed",
        "--stop",
        "--style",
        "--stylize",
        "--s",
        "--tile",
        "--niji",
        "--version",
        "--v"
    ))
    param = re.split(pattern, prompt)
    # # Print the matches
    #print(param)
    for _p in param:
        p =  _p.strip()
        if not p:
            continue
        elif p.startswith("--"):
            key,value = p.split(" ",1)
            if key in allowed_keys:
                unique_params[key] = value
        else:
            new_prompt += f"{p}"
    for k in unique_params:
        v = unique_params.get(k)
        if k == "--no" and v == space_name:
            continue
        else:
            new_prompt += f" {k} {v}"
    if "--no" in new_prompt:
        new_prompt = new_prompt.replace("--no", f"--no {space_name},")
    else:
        new_prompt += f" --no {space_name}"    

    ### replace image link
    new_prompt = re.sub(r"https://imgcdn.aipic.club/upload/", "http://imgcdn.aipic.club/upload/", new_prompt)
    return new_prompt

def get_prompt_from_content(content: str, space_name: str):
    content = re.sub(r"\*\*(.*?)\*\*(.*)", r"\1", content)
    if space_name not in content:
        return content
    else:
        pattern = r'--no\s(.*?)(?=\s--|$)'
        m = re.findall(r'--no\s(.*?)(?=\s--|$)', content)
        if len(m) == 1 and m[0] == space_name:
            content = re.sub(pattern, '', content)
        else:
            content = re.sub(f"{re.escape(space_name)}[\s,]+", "", content)
        return content



def add_zoom(prompt: str, zoom: float):
    prompt += f" --zoom {zoom}" 
    return prompt   



def get_worker_id(snowflake_id):
    return (snowflake_id >> 12) & 0x3FF


def generate_snowflake_id(date_string: str | None):
    # 41 bits for time in units of 10 msec
    # 10 bits for a sequence number
    # 12 bits for machine id
    epoch = 1420070400000
    gmt_dt = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z') if date_string else datetime.now()
    timestamp_ms = int((gmt_dt.timestamp() + utc_offset_seconds) * 1000)
    timestamp = timestamp_ms - epoch
    return (timestamp << 22)    

def get_uid_by_taskId(taskId : str) -> str:
    uid = taskId.split(".")[0]
    return uid

def get_dict_value(dct, keys):
    return reduce(lambda d, key: d.get(key) if d else None, keys.split("."), dct)


def is_imagine(content: str) -> str | None:
    return any(keyword in content for keyword in ["(relaxed)", "(relaxed, stealth)", "(fast)", "(fast, stealth)"])
    #return "(relaxed)"  in content or "(fast)" in content


def get_space_name(content: str) -> str | None:
    match = re.search(r"--no\s([\.\w]+)", content)
    if match:
        return match.group(1)
    return None
def is_committed(content: str) -> bool:
    return "(Waiting to start)" in content
def is_variation(content: str) -> bool:
    return  "Variations by" in content
def is_vary(content: str) -> bool:
    return "Variations (Strong) by" in content or "Variations (Subtle) by" in content
def is_remix(content: str) -> bool:
    return "Remix by" in content
def is_zoom(content: str) -> bool:
    return "Zoom Out by" in content
def is_pan(content: str) -> bool:
    return any(keyword in content for keyword in ["Pan Left by", "Pan Right by", "Pan Up by", "Pan Down by"])
def is_upsacle(content: str) -> bool:
    #Image #1
    return re.search(r"Image\s#\d", content)

    
def input_output_type(content: str) -> tuple[DetailType,DetailType] | None :
    if is_remix(content):
        return (
            DetailType.INPUT_MJ_REMIX,
            DetailType.OUTPUT_MJ_REMIX
        )
    elif is_variation(content):
        return (
            DetailType.INPUT_MJ_VARIATION,
            DetailType.OUTPUT_MJ_VARIATION
        )
    elif is_upsacle(content):
        return (
            DetailType.INPUT_MJ_UPSCALE,
            DetailType.OUTPUT_MJ_UPSCALE
        )
    elif is_vary(content):
        return (
            DetailType.INPUT_MJ_VARY,
            DetailType.OUTPUT_MJ_VARY
        )
    elif is_zoom(content):
        return (
            DetailType.INPUT_MJ_ZOOM,
            DetailType.OUTPUT_MJ_ZOOM
        )
    elif is_pan(content):
        return (
            DetailType.INPUT_MJ_PAN,
            DetailType.OUTPUT_MJ_PAN
        )
    elif is_imagine(content):
        return (
            DetailType.INPUT_MJ_IMAGINE,
            DetailType.OUTPUT_MJ_IMAGINE
        )    
    else:
        return (None, None)