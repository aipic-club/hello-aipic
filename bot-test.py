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
    timestamp_ms = int((gmt_dt.timestamp() + utc_offset_seconds) * 1000 + 125)
    timestamp = timestamp_ms - epoch
    return (timestamp << 22) ^ (1 << 18)     

# Example usage:


snowflake = Snowflake(1111703206368378880)
snowflake2 = Snowflake(1111703207668887634)

# snowflake3 = Snowflake(1111682555272503356)

print(snowflake.to_date)
print(snowflake2.to_date)
print(snowflake.timestamp)
print(snowflake2.timestamp)


print("====")
snowflake_id = generate_snowflake_id("Fri, 26 May 2023 17:02:27 GMT")

print(snowflake_id)
s = Snowflake(snowflake_id)

print(s.to_date)





# print(format(snowflake_id , "08b"))
# print(snowflake.to_binary)

# snowflake2 = Snowflake(snowflake_id)
# print(snowflake.to_date)
# print(snowflake2.to_date)
