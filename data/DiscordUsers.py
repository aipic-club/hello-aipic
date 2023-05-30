class DiscordUsers():
    def __init__(self, users:list) -> None:
        self.users = users
        self.uids = list(map(lambda u: u['uid'], users))
    def is_user_in_channel(self, guild_id: int, channel_id: int) -> bool:
        for u in self.users:
            if str(guild_id) == u['guild_id'] and str(channel_id) == u['channel_id']:
                return True
        return False
    def get_user_by_taskId(self, taskId : str):
        uid = taskId.split(".")[0]
        us =  list(filter(lambda u:  u['uid'] == uid, self.users))
        return us[0]   
    @property
    def authorizations(self):
        return list(map(lambda u: u['authorization'], self.users))