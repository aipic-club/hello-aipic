"""
add the taskId to the prompt 
add a meaningless word to parameter --no
"""

import re
from enum import Enum

from data import TaskStatus,OutputType


def refine_prompt(taskId: str, prompt: str):
    params = prompt.split()
    unique_params = {}
    new_prompt = ""
    for param in params:
        if param.startswith("--"):
            if " " in param:
                key, value = param.split(" ", 1)
            else:
                key = param
                value = ""
            if key not in unique_params:
                unique_params[key] = value
                new_prompt += f"{param} "
        else:
            new_prompt += f"{param} "
    if "--no" in new_prompt:
        new_prompt = new_prompt.replace("--no", f"--no {taskId},")
    else:
        new_prompt += f"--no {taskId}"
    return new_prompt.strip()

def is_draft(content: str) -> str | None:
    return "(relaxed)"  in content or "(fast)" in content

def get_taskId(content: str) -> str | None:
    match = re.search(r"--no\s(\w+)", content)
    if match:
        return match.group(1)
    return None
def is_committed(content: str) -> bool:
    return "(Waiting to start)" in content
def is_variations(content: str) -> bool:
    #Variations by
    return  "Variations by" in content
def is_upsacle(content: str) -> bool:
    #Image #1
    return re.search(r"Image\s#\d", content)



def status_type(content: str):
    if is_committed(content):
        return TaskStatus.COMMITTED
    elif output_type(content) is not None:
        return TaskStatus.FINISHED
    
def output_type(content: str):
    if is_draft(content):
        return OutputType.DRAFT
    elif is_variations(content):
        return OutputType.VARIATION
    elif is_upsacle(content):
        return OutputType.UPSCALE
    else:
        return None


