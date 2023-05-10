# This script ensures that host is set up correctly for docker to run, then runs the specified command:
# - Ensure directory volumes exist/are created on host with correct permissions (to avoid docker creating them as root)
# - Ensure file volumes exist on host with correct permissions (to avoid docker creating them as a directory)
# - Run the specified command with the correct environment variables set

import configparser
import os
import platform
import subprocess
import sys
from pathlib import Path


class MountPathError(Exception):
    pass


# Ensure we are running on Linux
if platform.system() != "Linux":
    raise RuntimeError("This script can only be run on Linux.")

if len(sys.argv) < 2:
    print(f"Usage: python {sys.argv[0]} <config_file>")
    sys.exit(1)


print("Setup started!")

config_file = sys.argv[1]

# Ensure config file exists
if not os.path.exists(config_file):
    raise RuntimeError(f"Config file {config_file} does not exist.")

print(f"Reading configuration: {config_file}")

# Read the configuration file
config = configparser.ConfigParser()
config.read(config_file)

# Get the required and optional mount paths
required_mount_paths = {
    name: Path(path).resolve() for name, path in config.items("required_mount_paths")
}

optional_directory_mount_paths = {
    name: Path(path).resolve()
    for name, path in config.items("optional_directory_mount_paths")
}

# Get the command to run
command_to_run = config.get("command", "command_to_run")

print("Checking paths ...")

# Check if required mounted paths exist
for name, path in required_mount_paths.items():
    if not os.path.exists(path):
        raise MountPathError(f"Error: {path} does not exist on the host.")

    print(f"Required path exists: {path}")


# Create optional mounted paths if they don't exist
for name, path in optional_directory_mount_paths.items():
    if not os.path.exists(path):
        print(f"Creating: {path}")
        os.makedirs(path)
    else:
        print(f"Optional path exists: {path}")


# Get the user and group IDs of the current user
# Assumes current user is the user that should also be used inside the container
user_id = os.getuid()  # type: ignore
group_id = os.getgid()  # type: ignore
print(f"Ensuring correct permissions for user {user_id}:{group_id} ...")

# Check and fix the ownership of both required and optional mounted paths
all_mount_paths = list(required_mount_paths.values()) + list(
    optional_directory_mount_paths.values()
)

for path in all_mount_paths:
    path_stat = os.stat(path)
    path_user_id = path_stat.st_uid
    path_group_id = path_stat.st_gid

    if path_user_id != user_id or path_group_id != group_id:
        print(f"Fixing ownership for {path} to user {user_id} and group {group_id}.")
        os.chown(path, user_id, group_id)  # type: ignore

# Make the mount paths and user/group IDs accessible to the command process as environment variables
for name, path in required_mount_paths.items():
    os.environ[name.upper()] = str(path)

for name, path in optional_directory_mount_paths.items():
    os.environ[name.upper()] = str(path)


os.environ["DOCKER_USER_ID"] = str(user_id)  # type: ignore
os.environ["DOCKER_GROUP_ID"] = str(group_id)  # type: ignore

print(f"Running command: {command_to_run}")

# Run the specified command
subprocess.run(command_to_run, shell=True, check=True)
