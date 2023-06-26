from datetime import datetime, timezone, timedelta

class Snowflake:
    def __init__(self, worker_id: int, epoch: int | None):
        self.worker_id = worker_id
        self.sequence = 0
        self.last_timestamp = -1
        self.epoch = epoch  if epoch is not None else 1420070400000

    def generate_id(self):
        current_timestamp = self._get_current_timestamp()

        print( current_timestamp)

        if current_timestamp < self.last_timestamp:
            raise Exception("Invalid system clock!")

        if current_timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 4095  # 12-bit sequence number
            if self.sequence == 0:
                current_timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = current_timestamp

        # Generate Snowflake ID
        snowflake_id = (
            (current_timestamp << 22) |
            (self.worker_id << 12) |
            self.sequence
        )
        return snowflake_id

    def _get_current_timestamp(self):
        gmt_dt = datetime.now(timezone(offset= timedelta(hours= 0)))
        return int((gmt_dt.timestamp()  * 1000)) - self.epoch

    def _wait_next_millis(self, last_timestamp):
        timestamp = self._get_current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._get_current_timestamp()
        return timestamp
    
    def parse_id(self, snowflake_id):
        timestamp = (snowflake_id >> 22) + self.epoch
        worker_id = (snowflake_id >> 12) & 0x3FF
        return timestamp, worker_id

    def get_timestamp(self, snowflake_id):
        timestamp, _ = self.parse_id(snowflake_id)
        return timestamp

    def get_worker_id(self, snowflake_id):
        _, worker_id = self.parse_id(snowflake_id)
        return worker_id

    @staticmethod
    def parse_snowflake_id( snowflake_id: int) -> int:
        worker_id = Snowflake.parse_snowflake_worker_id(snowflake_id=snowflake_id)
        broker_id , account_id = Snowflake.parse_worker_id(worker_id=worker_id)
        return broker_id , account_id

    @staticmethod
    def parse_snowflake_worker_id( snowflake_id: int) -> int:
        worker_id = (snowflake_id >> 12) & 0x3FF
        return worker_id
    # _ _ _ _ _ / _ _ _ _ _ 5 bits for broker id and 5 bits for account id
    # bot id and account id max value are both 31
    @staticmethod
    def generate_snowflake_worker_id( broker_id: int, account_id:int) -> int:
        return (broker_id << 5) | account_id
    @staticmethod
    def parse_worker_id( worker_id: int):
        broker_id  = worker_id >> 5
        account_id = worker_id & 0x1f
        return broker_id , account_id







