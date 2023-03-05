from datetime import time


class RecordingPeriod:
    name: str
    start_time: time
    end_time: time

    def __init__(self, name: str, start_time: time, end_time: time):
        if not name:
            raise ValueError("Name must not be empty")

        # Ensure start_time is before end_time
        if start_time > end_time:
            raise ValueError(f"Start time {start_time} must be before end time {end_time}")

        self.name = name
        self.start_time = start_time
        self.end_time = end_time


class Config:
    stream_url: str
    output_directory: str
    recording_periods: list[RecordingPeriod]

    def __init__(self, stream_url: str, output_directory: str, recording_times: list[RecordingPeriod]):
        if not stream_url:
            raise ValueError("Stream URL must not be empty")
        if not output_directory:
            raise ValueError("Output directory must not be empty")
        if not recording_times:
            raise ValueError("Recording periods must not be empty")

        self.stream_url = stream_url
        self.output_directory = output_directory
        self.recording_periods = recording_times
