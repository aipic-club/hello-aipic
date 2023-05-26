from snowflake import Snowflake
from datetime import datetime
import pytz

timezone = pytz.timezone('Asia/Shanghai')

date_object = datetime.now(timezone)
utc_offset_seconds = date_object.utcoffset().total_seconds()

def generate_snowflake_id(date_string: str ):
    # 41 bits for time in units of 10 msec
    # 10 bits for a sequence number
    # 12 bits for machine id

    epoch = 1420070400000
    gmt_dt = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')
    timestamp_ms = int((gmt_dt.timestamp() + utc_offset_seconds) * 1000)
    timestamp = timestamp_ms - epoch
    return (timestamp << 22)     

# Example usage:

snowflake_id = generate_snowflake_id("Fri, 26 May 2023 11:04:47 GMT")
snowflake = Snowflake(1111610882766667776)


print(format(snowflake_id , "08b"))
print(snowflake.to_binary)

snowflake2 = Snowflake(snowflake_id)
print(snowflake.to_date)
print(snowflake2.to_date)
