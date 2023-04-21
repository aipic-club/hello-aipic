import os
import yaml


file = open( os.path.join( os.getcwd(), 'users.yaml') , 'r', encoding="utf-8")
file_data = file.read()
file.close()
users = yaml.safe_load(file_data)
uids = list(map(lambda u: u['uid'], users))




def is_user_in_channel(guild_id: str, channel_id: str) -> bool:
    for u in users:
        if guild_id == u['guild_id'] and channel_id == u['channel_id']:
            return True
    return False

def get_user_by_taskId(taskId : str):
    uid = taskId.split(".")[0]
    us =  list(filter(lambda u:  u['uid'] == uid, users))
    return us[0]
