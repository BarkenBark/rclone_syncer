#!/bin/bash
# Parameters passed to script are passed to rclone sync, e.g. --progress.


# Get the directory in which this file resides.
# Works even if script called through symlnk. Credit: https://stackoverflow.com/a/246128
SOURCE="${BASH_SOURCE[0]:-$0}";
while [ -L "$SOURCE" ]; do # Resolve $SOURCE until the file is no longer a symlink.
  DIR="$( cd -P "$( dirname -- "$SOURCE"; )" &> /dev/null && pwd 2> /dev/null; )";
  SOURCE="$( readlink -- "$SOURCE"; )";
  [[ $SOURCE != /* ]] && SOURCE="${DIR}/${SOURCE}"; # If $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located.
done
SCRIPT_DIR="$( cd -P "$( dirname -- "$SOURCE"; )" &> /dev/null && pwd 2> /dev/null; )";

LOG_DIR=${SCRIPT_DIR}/log
CONFIG_DIR=${SCRIPT_DIR}/cfg
mkdir -p $LOG_DIR
mkdir -p $CONFIG_DIR

LOGFILE=${LOG_DIR}/rclone.log
RCLONE_REMOTE=$(cat ${CONFIG_DIR}/remote_name.txt)

# Exit if running.
if [[ "`pidof -x $(basename $0) -o %PPID`" ]]; then exit; fi

# Send sync start notification.
notify-send --urgency=low "Scheduled Sync" "Sync to remote started..."

# Iterate over JSON objects.
jq '.[]' ${CONFIG_DIR}/paths_to_sync.json -c | \
while IFS= read -r -d $'\n' path_to_sync; 
do 
	# Get JSON object properties.
	local_path=$(echo "$path_to_sync" | jq -r '.local_path'); 
	remote_path=$(echo "$path_to_sync" | jq -r '.remote_path');
	excludes=$(echo "$path_to_sync" | jq -r '.excludes');

	# Add exclude options if available.
	if [[ $excludes != null ]]
	then
		arr=( $(echo "$excludes" | jq '.[]' -c -r) )
		exclude_options=""
		for exclude in ${arr[@]}
		do
			exclude_options+="--exclude ${exclude} "
		done
	fi

	# Run rclone sync command.
	echo "Syncing local path ${local_path} ..."
	rclone sync $local_path ${RCLONE_REMOTE}:$remote_path \
	--create-empty-src-dirs --log-file $LOGFILE --log-level INFO \
	--exclude-if-present .barksync_ignore \
	$exclude_options \
	$@

done

# Send sync end notification.
notify-send --urgency=low "Scheduled Sync" "Sync to remote finished."