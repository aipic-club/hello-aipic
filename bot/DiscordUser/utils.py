from functools import reduce
from datetime import datetime
import pytz
from data import TaskStatus,OutputType
import re



timezone = pytz.timezone('Asia/Shanghai')

date_object = datetime.now(timezone)
utc_offset_seconds = date_object.utcoffset().total_seconds()

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
def is_variations(content: str) -> bool:
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
    
def output_type(content: str):
    if is_remix(content):
        return OutputType.REMIX
    elif is_variations(content):
        return OutputType.VARIATION
    elif is_upsacle(content):
        return OutputType.UPSCALE
    elif is_draft(content):
        return OutputType.DRAFT
    else:
        return None