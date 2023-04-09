# Stream2Podcast

Stream2Podcast lets you record audio streams (e.g. live radio) and create podcast feeds from the recordings.

## Features

-   Record an audio stream and save it to disk (works with audio streams following either ICY or HLS protocol)
-   Create multiple recording schedules to record at specific time intervals throughout the day
-   Generate podcast feed (XML-files) from the recordings produced by each schedule (i.e. turns a recording schedule into a podcast with each recording representing an episode)
-   Docker support: Easy deployment using Docker Compose
-   Publish as podcast: The output of `stream2podcast` makes it simple to set up a webserver (e.g. [Nginx](https://www.nginx.com/)) to serve the static files from the root of the output directory.

## Getting Started

**1. Clone the repository**:

```
git clone https://github.com/roedebaron/stream2podcast.git
cd stream2podcast
```

**2. Set up configuration**

The project consists of two services: `recording-service` and `feed-service`. The `recording-service` is responsible for recording the audio streams and storing them on disk, while the `feed-service` is responsible for generating podcast feeds based on these recordings. The two services run separately and are fully independent of each other. `feed-service` is simply monitoring the output directory of the `recording-service` for any changes, and will update the podcast feeds whenever a new recording is added.

### recording-service

`./recording-service/config.example.yml` provides an example of the required configuration format:

```yaml
stream_url: "https://example.com"
output_dir: "../recordings" # Directory where recordings should be saved
time_zone: "Europe/Berlin" # IANA time zone name. See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

# Time periods to record the stream every day
recording_schedules:
    - title: "morning program" # Will be used as the title of the podcast feed
      start_timeofday: "06:15" # Time as HH:MM (24-hour clock) in the specified time zone
      end_timeofday: "07:00"
      description: "This is a morning program" # Optional, will be used as the description of the podcast feed
      image_url: "https://example.com/image.png" # Optional, will be used as the image of the podcast feed

    - title: "afternoon program"
      start_timeofday: "13:05"
      end_timeofday: "14:00"

    - title: "evening program"
      start_timeofday: "19:30"
      end_timeofday: "21:00"
```

Rename the file to `config.yml` and adapt the configuration to your use case. Note that the start and end time for a recording schedule should not overlap with other recording schedules as the recording process occurs sequentially (alternatively, the overlapping schedule will start as soon as the other one finishes). If the service is started during a recording schedule, recording will start immediately.

### feed-service

`./feed-service/config.example.yml` provides an example of the required configuration format:

```yaml
base_dir: "../recordings" # Directory where feed-service should look for recordings
base_url: "https://podcasts.mydomain.com/" # Base URL where the podcast feeds should be served from
```

Rename the file to `config.yml` and adapt the configuration to your use case. The base directory should be set to the output directory used by `recording-service` (or any directory, as long as the contained files follows the file structure and name pattern specified in the **Usage** section).

Once the configuration files are set up, you can either run the program locally or using Docker Compose (see below).

## Local Installation 💻

\*Requires the [Poetry](https://python-poetry.org/docs/) package manager

First, cd into either `./recording-service` or `./feed-service` depending on which service you want to run.

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

-   You can specify a custom path for your configuration file using `./main.py -c path/to/config.yml`

## Docker 🐳

\*Requires [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

**3. From project root, navigate to the `./docker` folder**

```
cd docker
```

Inspect the configuration in `docker-compose.yml`, especially the volumes, and verify that the host paths match your file structure.

**4. Build and run the Docker Compose project**

```
docker-compose up --build
```

To prevent the container from running as root, you can set the `UID` environment variable to match the current user's ID. The Docker Compose configuration is set up such that it will run the container as this user rather than as root:

Bash:
`export UID && docker-compose up --build`

Powershell:
`$env:UID=$(id -u); docker-compose up --build`

NB: Remember this user must have the necessary permissions to access the volumes specified in `docker-compose.yml`.

## Output

### recording-service

The `recording-service` automatically starts recording the audio stream following the recording schedules as specified in `./recording-service/config.yml`. The service creates a new directory for each recording schedule for storing the recordings produced by that schedule together with a metadata file.

The file structure of the output directory is as follows:

```bash
<output_dir>/
│
├── <recording_schedule_1>/
│   ├── <recording_1>
│   ├── <recording_2>
│   ├── ...
│   └── metadata.yml
│
├── <recording_schedule_2>/
│   └── ...
└── ...
```

The name of a recording file follows the parsable and URL-friendly format:

`<date>--<start_time>-<end_time>--<name_of_recording>--<uuid>.mp3|mp4`

-   `<date>`: Date of recording in the format YYYY-MM-DD
-   `<start_time>`: Start time (UTC) of recording in the format HHMM (i.e. this can vary from the start time specified in the configuration file, if the service is started during a recording schedule)
-   `<end_time>`: End time (UTC) of recording in the format HHMM
-   `<name_of_recording>`: Sluggified name of the recording. (currently this is the same as the name of the recording schedule/podcast name)
-   `<uuid>`: A universally unique identifier (UUID)
-   `.mp3|mp4`: The file format, either .mp3 or .mp4

Example: `2023-04-03--1230-1400--recording-name--ee1ad7c6-95bf-4116-a1f8-060053e80a73.mp3`

### feed-service

The output of `recording-service` enables the `feed-service` to generate the corresponding podcast feeds. `feed-service` generates a podcast feed for each recording schedule, and each recording is represented as an episode in that feed. The resulting `feed.xml` file is saved in the same directory as the recordings. As such, the file structure of the output directory ends up looking like this:

```bash
<output_dir>/
│
├── <recording_schedule_1>/
│   ├── <recording_1>
│   ├── <recording_2>
│   ├── ...
│   ├── metadata.yml
│   └── feed.xml # <-- added by feed-service
└── ...
```
