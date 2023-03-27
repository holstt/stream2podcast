#!/bin/bash

# After configuration, this script will be able to upload and deploy the project on a remote server.

# USAGE:
# 1. Place this script in the root directory of the project
# 2. Configure the script by modifying the variables after "USER INPUT" below.
# 3. Run ./deploy.sh
# 4. Rsync will perform a dry run first. Please inspect the files that are going to be transferred and press Enter to confirm
#    The script will then transfer the files and run the specified command on the remote server.
# NB: Remember to upload any ignored env/secrets/config files to the server manually

# Exit script immediatly on any errors
set -e

#######################
##### SET BY USER #####
#######################
# This should be the name of the root dir of project on both local machine and remote server. Rsync will create the directory on the remote server if it doesn't exist
PROJECT_DIR_NAME="stream2podcast"
# Shell alias for the remote server or use username@remote_server_address
REMOTE_SERVER="vm1"
# Command that will run the program on the remote server
REMOTE_COMMAND="export CONFIG_PATH=../config.json UID && cd $PROJECT_DIR_NAME/docker && docker-compose up --build"

# Specify files to sync
# Modify the source_files and exclude_pattern arrays to include/exclude relevant files and folders.
source_files=(
  # Folders
  "--include=*/"
  "--include=src/**.py"
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
## END OF USER INPUT ##
#######################

# Set destination path to remote server (same name as project directory)
DEST="$REMOTE_SERVER:~/$PROJECT_DIR_NAME"

WORKING_DIR_NAME=$(basename "$PWD")

# --no-p, do not keep permissions
# -m is --prune-empty-dirs and is somehow important for rsync to exclude the correct files
RSYNC_COMMAND="-vam --no-p --progress "${source_files[@]}" "${exclude_pattern[@]}" . $DEST"

# This if statement prevents uploading the wrong folder :)
if [ "$WORKING_DIR_NAME" == "$PROJECT_DIR_NAME" ]; then
  # Run a dry run first
  echo "Running dry run... The following files will be transferred:"
  rsync --dry-run $RSYNC_COMMAND

  # Let user confirm
  echo "Press Enter to confirm file sync to $DEST, or Ctrl + C to cancel..."
  read

  # Copy files to server
  rsync $RSYNC_COMMAND
  echo "Sync complete"
else
  echo "Error: Expected name of working directory to be '$PROJECT_DIR_NAME', but name of working directory is '$WORKING_DIR_NAME'. No files have been transferred. Please ensure you are in the correct directory and try again."
  exit 1
fi

# Run command on remote server
echo "Running remote command on $REMOTE_SERVER..."
ssh $REMOTE_SERVER $REMOTE_COMMAND
