# MegaCMD-Extra-Tools

Install by cloning / downloading, then from inside the directory:
    
`sudo pip3 install .`


## mega-one-way-sync

Performs a one-off, one-way sync from a local directory to a remote directory.

* Files and directories found in the remote but not in the local will be deleted from the remote.
* All files found locally that don't exist or are different in the remote are uploaded.

### Arguments

`mega-one-way-sync LOCALDIR REMOTEDIR [EXCLUDE...]`

`LOCALDIR` - The path of the local directory

`REMOTEDIR` The path on the remote you want this directory synced *to* (not *into*)

`[EXCLUDE...]` An optional list of files/directories you don't want uploaded. These are paths relative to the local directory.

### Examples

`mega-one-way-sync /data/files Files dir1 dir2/file1`

This will result in `/data/files` being uploaded to the remote with name `Files`. The directory `/data/files/dir1` and `/data/files/dir2/file1` will not be uploaded.

### Caveats / TODO

* Only works with Linux / UNIX-like OSes
