import time

class SnowflakeGenerator:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.sequence = 0
        self.last_timestamp = -1

    def generate_id(self):
        current_timestamp = self._get_current_timestamp()

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
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp):
        timestamp = self._get_current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._get_current_timestamp()
        return timestamp
