import requests
MJAppID = "936929561302675456"
class Selfbot():
    def __init__(self, token, guildId, channelId):
        self.token = token
        self.guild = guildId
        self.channel = channelId
    def __sendInteractions(self, payload):
        header = {
            'authorization' : self.token
        }
        response = requests.post("https://discord.com/api/v9/interactions",json = payload, headers = header)
        return response
    def sendPrompt(self, prompt):
        payload = {
            "type":2,
            "application_id":MJAppID,
            "guild_id":"1084379543072149524",
            "channel_id":"1092323945614675999",
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version":"1077969938624553050","id":"938956540159881230",
                "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{"id":"994261739745050684","application_id":MJAppID,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
                "attachments":[]
            }
        }
        response = self.__sendInteractions(payload)
        print(response)
    def Upscale(index : int, messageId : str, messageHash : str):
        pass
    def MaxUpscale(messageId : str, messageHash : str):
        pass
    def Variation(index : int,messageId : str, messageHash : str):
        pass