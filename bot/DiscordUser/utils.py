from datetime import datetime
import pytz


timezone = pytz.timezone('Asia/Shanghai')

date_object = datetime.now(timezone)
utc_offset_seconds = date_object.utcoffset().total_seconds()

def generate_snowflake_id(date_string: str | None):
    # 41 bits for time in units of 10 msec
    # 10 bits for a sequence number
    # 12 bits for machine id
    epoch = 1420070400000
    gmt_dt = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')
    timestamp_ms = int((gmt_dt.timestamp() + utc_offset_seconds) * 1000)
    timestamp = timestamp_ms - epoch
    return (timestamp << 22)    