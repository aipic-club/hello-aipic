from functools import reduce
from datetime import datetime
import pytz
from data import TaskStatus,OutputType,DetailType
import re



timezone = pytz.timezone('Asia/Shanghai')

date_object = datetime.now(timezone)
utc_offset_seconds = date_object.utcoffset().total_seconds()



def refine_prompt(taskId: str, prompt: str):
    pattern = r'(--?\w+\s+[\w\.]+)+'
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
    for p in param:

        if p == " ":
            continue
        elif p.startswith("--"):
            key,value = p.split(" ",1)
            if key in allowed_keys:
                unique_params[key] = value
        else:
            new_prompt += f"{p}"
    for k in unique_params:
        ["--aspect", ""]
        new_prompt += f" {k} {unique_params.get(k)}"
    if "--no" in new_prompt:
        new_prompt = new_prompt.replace("--no", f"--no {taskId},")
    else:
        new_prompt += f" --no {taskId}"    
    return new_prompt



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


def is_draft(content: str) -> str | None:
    return "(relaxed)"  in content or "(fast)" in content

def get_taskId(content: str) -> str | None:
    match = re.search(r"--no\s([\.\w]+)", content)
    if match:
        return match.group(1)
    return None
def is_committed(content: str) -> bool:
    return "(Waiting to start)" in content
def is_variation(content: str) -> bool:
    #Variations by
    return  "Variations by" in content
def  is_remix(content: str) -> bool:
    return "Remix by" in content
def is_upsacle(content: str) -> bool:
    #Image #1
    return re.search(r"Image\s#\d", content)



def status_type(content: str):
    if is_committed(content):
        return TaskStatus.COMMITTED
    elif output_type(content) is not None:
        return TaskStatus.FINISHED
    
def output_type(content: str) -> DetailType | None:
    if is_remix(content):
        return DetailType.OUTPUT_MJ_REMIX
    elif is_variation(content):
        return DetailType.OUTPUT_MJ_VARIATION
    elif is_upsacle(content):
        return DetailType.OUTPUT_MJ_UPSCALE
    elif is_draft(content):
        return DetailType.OUTPUT_MJ_PROMPT
    else:
        return None