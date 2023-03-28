# Stream2Podcast

Stream2Podcast lets you record audio streams (e.g. live radio) and create a podcast feed from the recordings.

## Features

-   Record an audio stream and save it to disk
-   Configure the program to record at specified time periods throughout the day
-   Make recordings accessible in a private podcast feed (coming soon)

## Getting Started

**1. Clone the repository**:

```
git clone https://github.com/roedebaron/stream2podcast.git
cd stream2podcast
```

**2. Set up configuration**

`./config.example.json` provides an example of the configuration format:

```json
{
    "stream_url": "https://example.com",
    "output_dir": "recordings",
    "recording_schedules": [
        {
            "title": "morning program",
            "start_timeofday": "06:15",
            "end_timeofday": "07:00"
        },
        {
            "title": "afternoon program",
            "start_timeofday": "13:05",
            "end_timeofday": "14:00"
        },
        {
            "title": "evening program",
            "start_timeofday": "19:30",
            "end_timeofday": "21:00"
        }
    ]
}
```

Rename the file to `./config.json` and specify the URL for the audio stream, one or more `recording_schedules` defining the start and end times to record (**NB: time should be in UTC**), and the output directory where recordings should be saved. Note that the start and end time for a recording period is not allowed to overlap with other recording periods as the recording process occurs sequentially. If the program starts during a recording period, it will start recording immediatly.

Once the config file is set up, you can either run the program locally or using Docker Compose (see below).

## Local Installation 💻

\*Requires the [Poetry](https://python-poetry.org/docs/) package manager

**3. Install dependencies and create a virtual environment**

```
poetry install
```

**4. Activate the virtual environment**

```
poetry shell
```

**5. Run the project**

```
python ./main.py
```

-   You can specify a custom path for your configuration file using `./main.py -c path/to/config.json`

## Docker 🐳

\*Requires [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

**4. From project root, navigate to the `./docker` folder**

```
cd docker
```

Inspect the configuration in `docker-compose.yml`, especially the volumes, and verify that the host paths match your file structure.

**5. Build and run the Docker Compose project**

```
docker-compose up --build
```

To prevent the container from running as root, you can set the `UID` environment variable to match the current user's ID. The Docker Compose configuration is set up such that it will run the container as this user rather than as root:

Bash:
`export UID && docker-compose up --build`

Powershell:
`$env:UID=$(id -u); docker-compose up --build`

NB: Remember this user must have the necessary permissions to access the volumes specified in `docker-compose.yml`.

## Usage

The program automatically starts recording the audio stream each day during the time periods specified in `config.json`. Recordings are saved in the output directory in format `<date>__<start time>_(<actual start time>)-<end time>_<name of recording>.mp3`.

Enjoy!
