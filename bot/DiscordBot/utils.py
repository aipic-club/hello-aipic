# add the taskId to the prompt 
# add a meaningless word to parameter --no
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
    return new_prompt.strip()

