#!/usr/bin/python3

from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


remote_path_regex = re.compile(r'^(.+)\:$')
remote_file_regex = re.compile(r'^(.{4})\s+([\-0-9]+)\s+([\-0-9]+)\s+(\d\d\w\w\w\d\d\d\d)\s+(\d\d:\d\d:\d\d)\s+(.+)$')


def main():
    scriptpath = sys.argv.pop(0)
    if len(sys.argv) < 2:
        err("Needs minimum two arguments: LOCALDIR REMOTEDIR [EXCLUDE...]")
        sys.exit(1)
    local_dir = sys.argv.pop(0)
    remote_dir = sys.argv.pop(0)
    excludes = []
    mode = None
    while len(sys.argv) > 0:
        arg = sys.argv.pop(0)
        if arg == '--exclude':
            mode = 'exclude'
        elif mode is None:
            err("Unrecogised argument {}".format(arg))
            sys.exit(1)
        else:
            if mode == 'exclude':
                excludes.append(arg)
    sync(local_dir, remote_dir, excludes)

def sync(local_dir, remote_dir, excludes):
    local_dir = Path(local_dir).resolve(strict=True)
    remote_dir = posix_ensure_abs(PurePosixPath(remote_dir))
    out("Syncing from {} to {}".format(local_dir, remote_dir))

    # Find all actual local files/directories excluded by exclude globs
    excluded_paths = []
    for exclude in excludes:
        excluded_paths.extend(local_dir.glob(exclude))
    out("Excluding paths:")
    for excluded_path in excluded_paths:
        out("- {}".format(excluded_path))

    # Ensure remote directory exists
    cmd("mega-mkdir -p {}".format(remote_dir), ignore_errors=True)

    # Delete dirs/files in remote that don't exist in local
    to_delete = get_remote_to_delete(local_dir, remote_dir)
    for f in to_delete:
        out("Delete from remote: {}".format(f))
        cmd("mega-rm -rf \"{}\"".format(f))

    # Upload new/modified files to remote
    paths_to_upload = get_local_to_upload(local_dir, excluded_paths)
    for path_to_upload in paths_to_upload:
        remote_parent_dir = PurePosixPath(remote_dir, path_to_upload.relative_to(local_dir)).parent
        out("Upload {} into {}".format(path_to_upload, remote_parent_dir))
        cmd("mega-put -c \"{}\" \"{}\"".format(path_to_upload, remote_parent_dir))

def get_remote_to_delete(local_dir, remote_dir):
    path_list = []
    output = cmd("mega-ls -Rl {}".format(remote_dir))

    current_dir = None
    for line in output.split("\n"):
        remote_path_match = remote_path_regex.match(line)
        if remote_path_match:
            # Directory
            current_dir = posix_ensure_abs(PurePosixPath(remote_path_match.group(1)))
            if len(path_list) == 0 or path_list[-1] not in current_dir.parents:
                local_file_path = Path(local_dir, current_dir.relative_to(remote_dir))
                if not local_file_path.is_dir():
                    path_list.append(current_dir)
        else:
            remote_file_match = remote_file_regex.match(line)
            if remote_file_match:
                # Ignore directories as they're managed by above block
                attrs = remote_file_match.group(1)
                is_dir = attrs[0] == 'd'
                if not is_dir:
                    # File
                    file_name = remote_file_match.group(6)
                    file_path = PurePosixPath(current_dir, file_name)
                    if len(path_list) == 0 or path_list[-1] not in file_path.parents:
                        local_file_path = Path(local_dir, file_path.relative_to(remote_dir))
                        if not local_file_path.is_file():
                            path_list.append(file_path)

    return path_list

def get_local_to_upload(local_dir, excluded_paths):
    if len(excluded_paths) == 0:
        return [local_dir]

    found_exclude = False
    found_paths = []
    for path in local_dir.iterdir():
        matching_excluded_paths = []
        exclude_path = False

        for excluded_path in excluded_paths:
            if path == excluded_path:
                # This path *entirely* matches the exclude, so we exclude it
                found_exclude = True
                exclude_path = True
                break
            elif path in excluded_path.parents:
                # This dir *partially* matches the exclude, so we need to work out
                # what paths inside it we can upload
                found_exclude = True
                matching_excluded_paths.append(excluded_path)

        if not exclude_path:
            if len(matching_excluded_paths) > 0:
                found_paths.extend(get_local_to_upload(Path(local_dir, path), matching_excluded_paths))
            else:
                found_paths.append(path)

    if found_exclude:
        # We found some paths to exclude, so only return the ones we should upload
        return found_paths
    else:
        # No exclusions found, we can upload the entire dir
        return [local_dir]

def posix_ensure_abs(path):
    if not path.is_absolute():
        return '/' / path
    return path

def cmd(command, ignore_errors=False):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = result.stdout.decode('utf-8').rstrip("\n")
    stderr = result.stderr.decode('utf-8').rstrip("\n")
    if result.returncode != 0 and not ignore_errors:
        raise Exception("Command returned code {} - \"{}\"".format(result.returncode, stderr))
    return stdout

def out(message):
    print(message, flush=True)

def err(message):
    print(message, flush=True, file=sys.stderr)


if __name__ == '__main__':
    main()
