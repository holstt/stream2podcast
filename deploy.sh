#!/bin/bash


# This script will upload the relevant files in the project folder to a folder (of the same name) on the remote server
# 1. Place this script in project root folder and modify the "SET BY USER" variables below.
# 2. You may also modify the source_files and exclude_pattern arrays to include/exclude relevant files and folders
# 3. Run ./deploy.sh
# 4. Rsync will perform a dry run first. Please inspect the files that are going to be transferred and press Enter to confirm
#    The script will then transfer the files to the remote server and run the bot on the server using docker-compose
# NB: Remember to upload any ignored env/secrets/config files to the server manually


# Exit script immediatly on any errors
set -e

#######################
##### SET BY USER #####
#######################
PROJECT_DIR_NAME="stream2podcast"
REMOTE_SERVER="vm1" # Shell alias for the remote server or use username@remote_server_address
REMOTE_COMMAND="export CONFIG_PATH=../config.json && cd $PROJECT_DIR_NAME/docker && docker-compose up --build" # Command to run on the remote server

# Specify files to sync
source_files=(
  # Folders
  "--include=src/"
  "--include=src/**.py"
  "--include=docker/"
  "--include=docker/**"

  # Files
  "--include=main.py"
  "--include=pyproject.toml"
  "--include=poetry.lock"
)

# Specify excluded files
exclude_pattern=(
  "--exclude=*" # Exclude everything but the files and folders defined in source_files
)
#######################
#######################
#######################


# Set destination path to folder of same name as project on remote server
DEST="$REMOTE_SERVER:~/$PROJECT_DIR_NAME"

WORKING_DIR_NAME=$(basename "$PWD")

# This if statement prevents uploading the wrong folder :)
if [ "$WORKING_DIR_NAME" == "$PROJECT_DIR_NAME" ]; then
# Copy files to server
  echo "Running dry run... The following files will be transferred:"
  rsync -av --progress --dry-run "${source_files[@]}" "${exclude_pattern[@]}" . $DEST
  echo "Press Enter to confirm file sync to $DEST, or Ctrl + C to cancel..."
  read
  rsync -av --progress "${source_files[@]}" "${exclude_pattern[@]}" . $DEST
  echo "Sync complete"
else
  echo "Error: Expected name of working directory to be '$PROJECT_DIR_NAME', but name of working directory is '$WORKING_DIR_NAME'. No files have been transferred. Please ensure you are in the correct directory and try again."
  exit 1
fi

# Run command on remote server
echo "Running remote command on $REMOTE_SERVER..."
ssh $REMOTE_SERVER $REMOTE_COMMAND