import configparser
import os
import platform
import subprocess
import sys
from pathlib import Path

# pyright: reportTypeCommentUsage=false

# This script ensures that the host is set up correctly for the docker project to run, then runs the specified docker command. Specifically, it will:
# - Ensure directory volumes exist/are created on host with correct permissions (to avoid docker creating them as root)
# - Ensure file volumes exist on host with correct permissions (to avoid docker creating them as a directory)
# - Run the specified command with the correct environment variables set

# The script requires an ini configuration file (see 'example.ini')
# May require sudo depending on permissions of the mounted paths
# Example usage: python docker_run.py myconfig.ini

# Compatibility: Linux only, Python 3.5+


class MountPathError(Exception):
    pass


class Config:
    required_mount_paths = {}  # type: dict[str, Path]
    optional_directory_mount_paths = {}  # type: dict[str, Path]
    command_to_run = ""  # type: str


def main():
    # Ensure we are running on Linux
    if platform.system() != "Linux":
        raise RuntimeError("This script can only be run on Linux.")

    if len(sys.argv) < 2:
        print("Usage: python {} <config_file>".format(sys.argv[0]))
        sys.exit(1)

    print("Setup started!")

    config_file_path = Path(sys.argv[1]).resolve().as_posix()

    config = get_config(config_file_path)

    print("Checking paths ...")
    check_paths(config)

    # Get the user and group IDs of the current user
    # Assumes current user is the user that should also be used inside the container
    user_id = os.getuid()  # type: ignore
    group_id = os.getgid()  # type: ignore

    print("Checking permissions ...")
    check_permissions(config, user_id, group_id)  # type: ignore

    print("Setting environment ...")
    set_environment(config, user_id, group_id)  # type: ignore

    print("Running command: ", config.command_to_run)
    run_command(config.command_to_run)


def get_config(config_file_path: str) -> Config:
    parser = get_config_parser(config_file_path)

    required_mount_paths = {
        name: Path(path) for name, path in parser.items("required_mount_paths")
    }

    optional_directory_mount_paths = {
        name: Path(path)
        for name, path in parser.items("optional_directory_mount_paths")
    }

    command_to_run = parser.get("command", "command_to_run")

    parser = Config()
    parser.required_mount_paths = required_mount_paths  # type: ignore
    parser.optional_directory_mount_paths = optional_directory_mount_paths  # type: ignore
    parser.command_to_run = command_to_run  # type: ignore
    return parser


def get_config_parser(config_file: str) -> configparser.ConfigParser:
    if not os.path.exists(config_file):
        raise RuntimeError("Config file {} does not exist.".format(config_file))

    print("Reading configuration: ", config_file)

    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def check_paths(config: Config):
    # Check if required mounted paths exist
    for name, path in config.required_mount_paths.items():
        if not os.path.exists(path):
            raise MountPathError("Error: {} does not exist on the host.".format(path))

        print("Required path exists: ", path)

    # Create optional mounted paths if they don't exist
    for name, path in config.optional_directory_mount_paths.items():
        if not os.path.exists(path):
            print("Creating: ", path)
            os.makedirs(path)
        else:
            print("Optional path exists: ", path)


# Check and fix the ownership of both required and optional mounted paths
def check_permissions(config: Config, user_id: int, group_id: int):
    print("Ensuring correct permissions for user {}:{} ...".format(user_id, group_id))  # type: ignore

    all_mount_paths = list(config.required_mount_paths.values()) + list(
        config.optional_directory_mount_paths.values()
    )

    for path in all_mount_paths:
        path_stat = os.stat(path)
        path_user_id = path_stat.st_uid
        path_group_id = path_stat.st_gid

        if path_user_id != user_id or path_group_id != group_id:
            print("Fixing ownership for {} to user {} and group {}.".format(path, user_id, group_id))  # type: ignore
            os.chown(path, user_id, group_id)  # type: ignore


def set_environment(config: Config, user_id: int, group_id: int):
    # Make the mount paths and user/group IDs accessible to the command process as environment variables
    for name, path in config.required_mount_paths.items():
        os.environ[name.upper()] = str(path)

    for name, path in config.optional_directory_mount_paths.items():
        os.environ[name.upper()] = str(path)

    os.environ["DOCKER_USER_ID"] = str(user_id)  # type: ignore
    os.environ["DOCKER_GROUP_ID"] = str(group_id)  # type: ignore


def run_command(command: str):
    subprocess.run(command, shell=True, check=True)


if __name__ == "__main__":
    main()
