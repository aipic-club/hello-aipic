import random
import string
from datetime import datetime
import pytz

def random_id(length = 6) -> str:
    all = string.ascii_letters + string.digits
    # all = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.sample(all,length))

def current_time() -> str:
    current_time_utc = datetime.now(pytz.UTC) 
    return current_time_utc.strftime("%Y-%m-%d %H:%M:%S")
def is_expired(t: any) -> bool:
    current_time_utc = datetime.now(pytz.UTC) 
    given_time =  t.replace(tzinfo=pytz.UTC)
    return given_time < current_time_utc