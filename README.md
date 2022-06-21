# Setting up periodic sync of files and folders to cloud storage using `rclone`

## Setup

### 1. Follow [these instructions](https://itsfoss.com/use-onedrive-linux-rclone/) to install `rclone` and add your cloud storage system as a remote to `rclone`

Shortly summarized, the steps are as follows:

1. `sudo apt install rclone`
2. `rclone config`
   - Add a new remote to your cloud storage system, e.g. OneDrive.

### 2. Run `install.sh`

Run `sudo ./install.sh <<REMOTE_NAME>>` where `<<REMOTE_NAME>>` is the name of the remote added in the previous step.

- You can list all available remotes in `rclone` by running `rclone config`.

`install.sh` will add the following commands to */usr/bin* (symbolic links to scripts in this directory) and add a crontab to run the first listed command at a regular interval:

- `barksync_sync` - Syncs all files specified in the list of paths to sync (see section [List of paths to sync](#list-of-paths-to-sync-cfgpaths_to_syncjson)) to the remote.
- `barksync_add` - Adds path(s) to list of paths to sync. *Requires `python`.*
- `barksync_exclude` - Excludes path(s) from being synced by adding a *.barksync_ignore* file to the path(s). *Requires `python`.*

For more information, run the commands with the `--help` flag.

## Usage and explanation

After installation, `barksync_sync` will be run as a cronjob once every day at 11:30, syncing the paths specified in the [list of paths to sync](#list-of-paths-to-sync-cfgpaths_to_syncjson). It is also possible to run the command manually. Any arguments passed to `barksync_sync` will be passed to the underlying `rclone sync` command.

Any paths specified below are relative to this repository root.

### List of paths to sync (*cfg/paths_to_sync.json*)

- The file is a JSON array where each item has the following properties:

  - `local_path` - Absolute path to file/folder on local machine to sync to remote.
  - `remote_path` - Absolute path to file/folder on remove machine.
  - (optional) `excludes` - List of exclude patterns to apply when syncing this path using `rclone`. See the [`rclone` documentation](https://rclone.org/filtering/) for an explanation of the patterns.

- The file can e.g. look like:

  ```json
  [
   {
    "local_path": "/home/user/path/to/directory1",
    "remote_path": "backup/home/user/path/to/directory1"
   },
   {
    "local_path": "/home/user/path/to/file1.txt",
    "remote_path": "backup/home/user/path/to"
   },
   {
    "local_path": "/home/user/path/to/directory2",
    "remote_path": "backup/home/user/path/to/custom_name_of_directory_2"
   },
   {
    "local_path": "/home/user/path/to/directory3",
    "remote_path": "backup/home/user/path/to/directory1",
    "excludes": [
      "big_heavy_data/**"
    ]
   }
  ]
  ```

- **Note:** Directories which do not exist on the remote will be created.

- **Note:** `remote_path` will always be a directory. Therefore, if `local_path` points to a regular file, the `remote_path` needs should point to the target directory on the cloud storage in which to place the synced file.

- **Note:** In the example above, any directory named *big_heavy_data* found at any depth within */home/user/path/to/directory3* would be excluded from sync.

### Modifying the list of paths to sync with `barksync_add`

The list of paths to sync may be modified manually. However, after setup you can use the command `barksync_add` to add a set of paths to the file programatically.

The command accepts one or several local paths which will be added with a remote path mirroring the absolute local path with a machine name based prefix. E.g. if the local absolute path is */home/user/.config/sublime-text*, the remote path will be *MYPC_backup/home/user/.config/sublime-text* assuming the machine name is `MYPC`. If the local path is a regular file, the remote path will resolve to the parent of that file.

By running the command with no positional arguments, the current directory is added.

### Excluding paths to sync with *.barksync_ignore* files

Any directory which contains a file named *.barksync_ignored* will be excluded from synchronization. Such a file can be added using the `barksync_exclude` command. The files may also be removed by using the `barksync_add` command with the `--unexclude` option.

### Log file

Logs from the underlying `rclone sync` command invoked by `barksync_sync` are saved to *log/rclone.log*.

# TO DO

- [ ] Notify user if file not found when syncing.
- [ ] Add a *.barksync_sync* file system?
  - Periodically scan selected directories for subdirectories containing *.barksync_sync* files to sync.
  - The *.barksync_sync* files may contain exclusion filters.
  - Could potentially just have a single *.barksync* file which contains exclusion filters.
    - Any folder with a *.barksync* file will be synced.
    - Could pass to *.barksync* to `--exclude-from` flag in `rclone sync`.
- [ ] Use [Argh](https://pypi.org/project/argh/) to create a proper CLI tool rather than having different symlinks to different scripts.
- [ ] Add dry run to path exclusion script.
