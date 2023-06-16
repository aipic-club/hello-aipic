from .values import MJBotId
class payloads:
    @staticmethod
    def prompt(ids: dict[str, str], prompt: str, nonce: int):
        return {
            **ids,
            "type":2,
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version":"1077969938624553050","id":"938956540159881230",
                "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{"id":"994261739745050684","application_id": MJBotId,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
                "attachments":[]
            },
            "nonce": nonce
        }

    @staticmethod
    def prompt_v1118961510123847772(ids: dict[str, str], prompt: str, nonce: int):
        return {
            **ids,
            "type":2,
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version": "1118961510123847772",
                "id": "938956540159881230",
                "name":"imagine",
                "type":1,
                "options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{
                    "id": "938956540159881230",
                    "application_id": MJBotId,
                    "version": "1118961510123847772",
                    "default_member_permissions": None,
                    "type":1,
                    "nsfw":False,
                    "name":"ask",
                    "description": "Create images with Midjourney",
                    "dm_permission":True,
                    "contexts": [
                        0,
                        1,
                        2
                    ],
                    "options":[
                        {
                            "type":3,
                            "name": "prompt",
                            "description": "The prompt to imagine",
                            "required":True
                        }
                    ]
                },
                "attachments":[]
            },
            "nonce": nonce
        }   

    @staticmethod
    def variation(ids: dict[str, str],  messageId : str, messageHash : str, index: int, nonce: int):
        return {
            **ids,
            "type": 3, 
            "message_flags":0,
            "message_id": messageId,
            "session_id":"1f3dbdf09efdf93d81a3a6420882c92c",
            "data":{
                "component_type":2,
                "custom_id": f"MJ::JOB::variation::{index}::{messageHash}"
            },
            "nonce": nonce
        }
    @staticmethod
    def remix(ids: dict[str, str], prompt: str, data_id: int, messageHash : str, index: int):
       return {
           **ids,
            "type":5,
            "data":{
                "id": data_id,
                "custom_id": f"MJ::RemixModal::{messageHash}::{index}",  #  "MJ::RemixModal::548034f0-49db-43fb-86f8-1ca09a72e786::1",
                "components":[
                    {
                        "type":1,
                        "components":[
                            {
                                "type":4,
                                "custom_id":"MJ::RemixModal::new_prompt",
                                "value": prompt
                            }
                        ]
                    }
                ]
            },
            "session_id":"1f3dbdf09efdf93d81a3a6420882c92c",
       } 
    
    @staticmethod
    def upscale(ids: dict[str,str], messageId : str, messageHash : str, index: int, nonce: int):
        return {
            **ids,
            "type":3,
            "message_flags":0,
            "message_id": messageId,
            "session_id":"45bc04dd4da37141a5f73dfbfaf5bdcf",
            "data":{
                "component_type":2,
                "custom_id": f"MJ::JOB::upsample::{index}::{messageHash}"
            },
            "nonce": nonce
        }
