import os
import asyncio
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())




# a = 1
# b = 31
# c = ((1 << 5) - 1 ) << 5
# print(hex(c))
# #c = a << 5 & b
# print("mask")
# print( format(c, "010b"))
# d =  (a << 5) & 0x3e0 | b
# print( format(d, "010b"))
# print(d)


# _ _ _ _ _ / _ _ _ _ _ 5 bits for bot id and 5 bits for account id
# note bot id and account id max value are both 31
def snowflake_worker_id(celery_worker_id: int, discord_account_id) -> int:
    mask = 0x3e0 # ((1 << 5) - 1 ) << 5
    return (celery_worker_id << 5) & mask | discord_account_id














