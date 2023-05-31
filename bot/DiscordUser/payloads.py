from .values import MJBotId
from .utils import generate_snowflake_id
class payloads:
    @staticmethod
    def prompt(ids: dict[str, str], prompt):
        return {
            **ids,
            "type":2,
            "application_id": MJBotId,
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version":"1077969938624553050","id":"938956540159881230",
                "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{"id":"994261739745050684","application_id": MJBotId,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
                "attachments":[]
            },
            "nonce": str(generate_snowflake_id(None))
        }