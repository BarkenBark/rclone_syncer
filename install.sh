#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "Install script needs to be run as root."
  exit
fi

if [ $# -eq 0 ]
  then
    echo "No arguments supplied. Supply the name of the rclone remote to sync paths to."
    exit
fi

# Get directory in which this file resides.
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";

# Create empty config directory if it doesn't exist.
CONFIG_DIR=${SCRIPT_DIR}/cfg
mkdir -p ${CONFIG_DIR}

# Store remote name.
echo $1 > ${CONFIG_DIR}/remote_name.txt

# Create empty list of paths to sync if it doesn't already exist.
PATHS_TO_SYNC_JSON_PATH=${CONFIG_DIR}/paths_to_sync.json
if test -f $PATHS_TO_SYNC_JSON_PATH
then
  echo "Found existing list of paths to sync at ${PATHS_TO_SYNC_JSON_PATH}. Will not overwrite."
else
  echo "Creating empty list of paths to sync at ${PATHS_TO_SYNC_JSON_PATH}"
  echo "[]" > $PATHS_TO_SYNC_JSON_PATH
fi

# Install sync tool.
ln -s ${SCRIPT_DIR}/sync_paths.sh /usr/bin/barksync_sync
echo "Created link /usr/bin/barksync_sync -> ${SCRIPT_DIR}/sync_paths.sh"

# Add crontab for sync tool. # Will run once every hour.
# For some reason I can't get the crontab to work with user root. Using $(logname) gets
# the username of the user who called the install.sh script, even when using sudo.
# Setting XDG_RUNTIME_DIR is necessary for notification to display to the user.
echo "SHELL=/bin/bash" > /etc/cron.d/sync_paths
echo "0 * * * * $(logname) XDG_RUNTIME_DIR=/run/user/\$(id -u) /usr/bin/barksync_sync" > /etc/cron.d/sync_paths
echo "Added crontab /etc/cron.d/sync_paths."

# Install additional tools for managing paths to sync. Require python to use.
ln -s ${SCRIPT_DIR}/tools/add_path_to_sync.py /usr/bin/barksync_add
ln -s ${SCRIPT_DIR}/tools/exclude_path_to_sync.py /usr/bin/barksync_exclude
