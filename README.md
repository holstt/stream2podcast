# Stream2Podcast

Stream2Podcast lets you record audio streams (e.g. live radio) and create a podcast feed from the recordings.

## Features

-   Record an audio stream and save it to disk
-   Configure the program to record at specified time periods throughout the day
-   Make recordings accessible in a private podcast feed (coming soon)

## Setup & Configuration

1. Clone the repository:

```
git clone https://github.com/roedebaron/stream2podcast.git
cd stream2podcast
```

2. Set configuration

A JSON config file specifies the URL for the audio stream, the time periods to record (remember time should be in UTC!), and the output directory for the saved recordings.

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

Once the config file is set up, you can either run the program locally or using docker-compose.

### Local installation

\*Requires the Poetry package manager

3. Install dependencies (creates a virtual env):

```
poetry install
```

4. Activate the virtual environment

```
poetry shell
```

5. Run

```
python ./main.py
```

-   You can specify a custom path for your configuration file using `./main.py --config path/to/config.json`

### Docker Setup

\*Requires Docker and docker-compose

4. From project root, navigate to docker folder

```
cd docker
```

5. Run

```
docker-compose up --build
```

## Usage

The program automatically starts recording the audio stream each day during the time periods specified in `config.json`. Recordings are saved in the output directory in format `YYYY-MM-DD__HH-MM-SS_name_of_recording.mp3`.

Enjoy!
