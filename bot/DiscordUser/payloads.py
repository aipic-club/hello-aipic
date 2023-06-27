from .values import MJ_VARY_TYPE, MJBotId
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
    def prefer_suffix(ids: dict[str, str],  nonce: int):
        return {
            "type":2,
            **ids,
            "session_id":"674cb1c3cdf93533745fefc9fd78838f",
            "data":{
                "version":"1121575372539039776",
                "id":"984273800587776053",
                "name":"prefer",
                "type":1,"options":[
                    {
                        "type":1,
                        "name":"suffix",
                        "options":[]
                    }
                ],
                "application_command":{
                    "id":"984273800587776053",
                    "application_id": str(MJBotId),
                    "version":"1121575372539039776",
                    "default_member_permissions": None,
                    "type":1,
                    "nsfw":False,
                    "name":"prefer",
                    "description":"…",
                    "dm_permission":True,
                    "contexts":None,
                    "options":[
                        {
                            "type":2,
                            "name":"option",
                            "description":"…",
                            "options":[
                                {
                                    "type":1,
                                    "name":"set",
                                    "description":"Set a custom option.",
                                    "options":[
                                        {
                                            "type":3,
                                            "name":"option",
                                            "description":"…",
                                            "required":True,
                                            "autocomplete":True,
                                        },
                                        {
                                            "type":3,
                                            "name":"value",
                                            "description":"…"
                                        }
                                    ]
                                },
                                {
                                    "type":1,
                                    "name":"list",
                                    "description":"View your current custom options."
                                }
                            ]
                        },
                        {
                            "type":1,
                            "name":"auto_dm",
                            "description":"Whether or not to automatically send job results to your DMs."
                        },
                        {
                            "type":1,
                            "name":"suffix",
                            "description":"Suffix to automatically add to the end of every prompt. Leave empty to remove.",
                            "options":[
                                {
                                    "type":3,
                                    "name":"new_value",
                                    "description":"…"
                                }
                            ]
                        },
                        {
                            "type":1,
                            "name":"remix",
                            "description":"Toggle remix mode."
                        }
                    ]
                },
                "attachments":[]
            },
            "nonce": nonce
        }

    @staticmethod
    def info(ids: dict[str, str],  nonce: int):
        return {
            "type":2,
            **ids,
            "session_id":"674cb1c3cdf93533745fefc9fd78838f",
            "data":{
                "version":"1118961510123847776",
                "id":"972289487818334209",
                "name":"info",
                "type":1,
                "options":[],
                "application_command":{
                    "id":"972289487818334209",
                    "application_id": str(MJBotId),
                    "version":"1118961510123847776",
                    "default_member_permissions":None,
                    "type":1,
                    "nsfw":False,
                    "name":"info",
                    "description":"View information about your profile.",
                    "dm_permission":True,
                    "contexts":[0,1,2]
                },
                "attachments":[]
            },
            "nonce": nonce
        }
    @staticmethod
    def describe(ids: dict[str, str], filename: str, uploaded_filename: str, nonce: int):
        return {
            "type":2,
            **ids,
            "session_id":"b65de01dc829af94e28335dd38599517",
            "data":{
                "version":"1118961510123847774",
                "id":"1092492867185950852",
                "name":"describe",
                "type":1,
                "options":[
                    {
                        "type":11,
                        "name":"image",
                        "value":0
                    }
                ],
                "application_command":{
                    "id":"1092492867185950852",
                    "application_id": str(MJBotId),
                    "version":"1118961510123847774",
                    "default_member_permissions":None,
                    "type":1,
                    "nsfw":False,
                    "name":"describe",
                    "description":"Writes a prompt based on your image.",
                    "dm_permission": True,
                    "contexts":[0,1,2],
                    "options":[
                        {
                            "type":11,
                            "name":"image",
                            "description":"The image to describe",
                            "required":True
                        }
                    ]
                },
                "attachments":[
                    {
                        "id":"0",
                        "filename": filename,
                        "uploaded_filename": uploaded_filename
                    }
                ]
            },
        "nonce":  nonce
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
    
    #### MJ 风控
    @staticmethod
    def appeal(ids: dict[str,str], messageId : str, custom_id: str,  nonce: int):
        return {
            **ids,
            "type":3,
            "nonce": nonce,
            "message_flags":64,
            "message_id": messageId,
            "session_id":"6e5e35098c7a55166f73ab21ee06875e",
            "data":{
                "component_type":2,
                "custom_id": custom_id
            }
        }



    # {"type":3,"nonce":"1122489989028904960","guild_id":"1121633108689698856","channel_id":"1121633108689698859","message_flags":64,"message_id":"1122489887665430589","application_id":"936929561302675456","session_id":"6e5e35098c7a55166f73ab21ee06875e","data":{"component_type":2,"custom_id":"MJ::Prompts::Appeal::OqWLXki2ZMU"}}

    @staticmethod
    def vary(ids: dict[str,str], type: MJ_VARY_TYPE , messageId : str, messageHash : str,  nonce: int):
        return {
            "type":3,
            "nonce":str(nonce),
            **ids,
            "message_flags":0,
            "message_id": messageId,
            "session_id":"42c6e0ad8006f8c0b457f8d480d7ac9f",
            "data":{
                "component_type":2,
                "custom_id": f"MJ::JOB::{MJ_VARY_TYPE.value}::1::{messageHash}::SOLO" 
            }
        }
    #custom_id: MJ::JOB::low_variation::1::6e3ee661-7947-4bf7-b42c-4ea9290d54cf::SOLO
    #custom_id: MJ::JOB::high_variation::1::6e3ee661-7947-4bf7-b42c-4ea9290d54cf::SOLO
    @staticmethod
    def zoom(ids: dict[str,str], messageId : str, messageHash : str,  nonce: int):
        return {
            "type":3,
            "nonce": str(nonce),
            **ids,
            "message_flags":0,
            "message_id": messageId,
            "session_id":"42c6e0ad8006f8c0b457f8d480d7ac9f",
            "data":{
                "component_type":2,
                "custom_id": f"MJ::Outpaint::75::1::{messageHash}::SOLO"
            }
        }
    ## 2x > 50 , 1.5x > 75
    @staticmethod
    def custom_zoom_step_1(ids: dict[str,str], messageId : str, messageHash : str,  nonce: int):
        return {
            "type":3,
            **ids,
            "nonce": str(nonce),
            "message_flags":0,
            "message_id": messageId,
            "session_id":"42c6e0ad8006f8c0b457f8d480d7ac9f",
            "data":{
                "component_type":2,
                "custom_id": f"MJ::CustomZoom::{messageHash}"
            }
        }
    @staticmethod
    def custom_zoom_step_2(ids: dict[str,str], value: str, messageHash : str,  nonce: int):
        return {
            "type":5,
            **ids,
            "data":{
                "id":"1123142966077304853",
                "custom_id": f"MJ::OutpaintCustomZoomModal::{messageHash}",
                "components":[
                    {
                        "type":1,
                        "components":[
                            {
                                "type":4,
                                "custom_id":"MJ::OutpaintCustomZoomModal::prompt",
                                "value": value #"Skulls, by Jon Burgerman --v 5.2 --no QV5xbSPJMRX --ar 1:1 --zoom 1.1"
                            }
                        ]
                    }
                ]
            },
            "session_id":"42c6e0ad8006f8c0b457f8d480d7ac9f",
            "nonce": str(nonce)
        }
    @staticmethod
    def square(ids: dict[str,str],):
        return (

        )
