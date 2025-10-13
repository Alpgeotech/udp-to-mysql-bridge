import time
import queue
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
# TODO: Does this need to be a class? 
    def __init__(self):
        pass

    def __process_data(self, data: list) -> dict:
        if len(data) == 0:
            return 0

        timestamps, samples = zip(*data)

        samples_count = len(samples)


        offset = sum(samples) / samples_count

        # Center samples around zero and take absolute values
        samples = [x - offset for x in samples]
        samples = [abs(x) for x in samples]

        lowest_datapoint = int(min(samples))
        highest_datapoint = int(max(samples))

        timestamp_of_first_sample = min(timestamps)
        timestamp_of_last_sample = max(timestamps)

        mean = int(sum(samples) / samples_count)

        return {
            "first_timestamp": timestamp_of_first_sample,
            "last_timestamp": timestamp_of_last_sample,
            "count": samples_count,
            "min": lowest_datapoint,
            "mean": mean,
            "max": highest_datapoint,
        }

    def cleanup_dataset(self, dataset):
        dataset = dataset.strip("{}")
        dataset = dataset.split(", ")
        channel_identifier = dataset[0].strip("'")
        timestamp = float(dataset[1])
        dataset = dataset[2:]
        dataset = list(map(int, dataset))

        return channel_identifier, timestamp, dataset
    
    def generate_message(self, channel_identifier: str, data: list) -> str: 
        data = self.__process_data(data)

        message = ";".join(
            [channel_identifier] + [str(data[key]) for key in [
                "first_timestamp",
                "last_timestamp",
                "count",
                "min",
                "mean",
                "max"
            ]]
        )
        message += '\n'

        return message

class DataBuffer:
    def __init__(self, identifier, averaging_duration):
        self.channel_identifier = identifier
        self.averaging_duration = averaging_duration
        self._buffer = queue.SimpleQueue()
        self._last_cleared = time.time()


    def add_dataset(self, timestamp, dataset):
        for sample in dataset:
            self._buffer.put((timestamp, sample))
        logger.debug(f"Dataset added to {self.channel_identifier} buffer.")

    def fetch_data_and_clear(self):        
        data = self.__fetch_data()
        self.__clear()

        logger.info(f"{self.channel_identifier} buffer fetched and cleared.")
        return data

    def __fetch_data(self):
        data = []
        while not self._buffer.empty():
            data.append(self._buffer.get())
        return data

    def __clear(self):
        self._last_cleared = time.time()

        self._udp_timestamp_first_sample = 0
        self._udp_timestamp_latest_sample = 0


    def time_since_last_clear(self):
        return time.time() - self._last_cleared

    def data_ready(self):
        if self._buffer.empty():
            logger.debug(f'{self.channel_identifier} buffer is empty.')
            return False
        
        if self.time_since_last_clear() < self.averaging_duration:
            logger.debug(f'{self.channel_identifier}buffer: averaging_duration has not passed yet.')
            return False
        
        return True
