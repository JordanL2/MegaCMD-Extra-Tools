# MegaCMD-Extra-Tools

Install by cloning / downloading, then from inside the directory:
    
`sudo pip3 install .`


## mega-sync-one-way

Performs a one-off, one-way sync from a local directory to a remote directory.

* Files and directories found in the remote but not in the local will be deleted from the remote.
* All files found locally that don't exist or are different in the remote are uploaded.

It's recommended to first use the `--dryrun` argument to show what actions will be taken, before performing the actual sync.

### Usage

```
usage: mega-sync-one-way [-h] [-e [EXCLUDES ...]] [-d] local_dir remote_dir

positional arguments:
  LOCALDIR              local directory to sync to remote
  REMOTEDIR             remote location to sync local directory

optional arguments:
  -h, --help            show this help message and exit
  -e [EXCLUDES ...], --exclude [EXCLUDES ...]
                        list of file patterns to exclude from sync
  -d, --dryrun          output list of actions to be taken, but don't do anything
```

### Examples

`mega-sync-one-way /data/files Files --exclude dir1 dir2/file1 **/*.jpg`

This will result in `/data/files` being uploaded/synced to the remote with name `Files`. The directory `/data/files/dir1`, the file `/data/files/dir2/file1`, and all *.jpg files in all sub-directories will not be uploaded.

### Caveats / TODO

* Only tested on Linux, Windows should theoretically work
