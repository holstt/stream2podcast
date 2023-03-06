# Stream2Podcast

Stream2Podcast lets you record audio streams (e.g. live radio) and create a podcast feed from the recordings.

## Features

-   Record an audio stream and save it to disk
-   Configure the program to record at specified time periods throughout the day
-   Make recordings accessible in a private podcast feed (coming soon)

## Installation

\*Requires the Poetry package manager

Clone the repository and install the dependencies by running:

```
git clone https://github.com/roedebaron/stream2podcast.git
cd stream2podcast
poetry install
poetry shell # Activate the project's virtual environment
```

## Configuration

Stream2Podcast expects a config file in JSON format that specifies the live stream URL, the time periods to record (remember time should be in UTC!), and the output directory for the saved recordings.

Note that the time periods cannot overlap as the recording process occurs sequentially.

Modify `./config.example.json` and rename it to `./config.json`:

```json
{
    "stream_url": "https://example.com",
    "output_dir": "recordings",
    "recording_periods": [
        {
            "name": "morning program",
            "start_time_utc": "06:15",
            "end_time_utc": "07:00"
        },
        {
            "name": "afternoon program",
            "start_time_utc": "13:05",
            "end_time_utc": "14:00"
        },
        {
            "name": "evening program",
            "start_time_utc": "19:30",
            "end_time_utc": "21:00"
        }
    ]
}
```

## Usage

Once the config.json file is set up, you can start the recording process by running the following command while in the virtual environment:

```
python ./main.py
```

The program will record the audio stream during the specified time periods every day and save the recorded segments to the output directory. Enjoy!
