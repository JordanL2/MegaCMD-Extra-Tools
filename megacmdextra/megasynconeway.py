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
    
    excluded_paths = []
    for exclude in excludes:
        excluded_paths.extend(local_dir.glob(exclude))
    out("Excluding paths:")
    for excluded_path in excluded_paths:
        out("- {}".format(excluded_path))
    
    # Make remote dir
    cmd("mega-mkdir -p {}".format(remote_dir), ignore_errors=True)
    
    # Delete dirs/files in remote that don't exist in local
    remote_files = get_remote_files(remote_dir)
    to_delete = []
    for f in remote_files:
        remote_file_path = f[0]
        is_dir = f[1]
        local_file_path = local_dir
        for p in remote_file_path.parts[2:]:
            local_file_path = local_file_path / p
        if is_dir:
            if not local_file_path.is_dir():
                to_delete.append(remote_file_path)
        else:
            if not local_file_path.is_file():
                to_delete.append(remote_file_path)
    
    to_delete = remove_redundant_paths(to_delete)
    for f in to_delete:
        out("Delete from remote: {}".format(f))
        cmd("mega-rm -rf \"{}\"".format(f))
    
    # Upload new/modified files to remote
    paths_to_upload = calculate_dirs_to_upload(local_dir, excluded_paths)
    for path_to_upload in paths_to_upload:
        remote_parent_dir = PurePosixPath(remote_dir, path_to_upload.relative_to(local_dir)).parent
        out("Upload {} into {}".format(path_to_upload, remote_parent_dir))
        cmd("mega-put -c \"{}\" \"{}\"".format(path_to_upload, remote_parent_dir))

def calculate_dirs_to_upload(local_dir, excluded_paths):
    if len(excluded_paths) == 0:
        return [local_dir]

    found_exclude = False
    found_dirs = []
    for d in local_dir.iterdir():
        matching_excluded_paths = []
        exclude_dir = False
        
        for excluded_path in excluded_paths:
            if d == excluded_path:
                # This dir *entirely* matches the exclude, so we exclude it
                found_exclude = True
                exclude_dir = True
                break
            elif d in excluded_path.parents:
                # This dir *partially* matches the exclude, so we need to work out
                # what dirs/files inside it we can upload
                found_exclude = True
                matching_excluded_paths.append(excluded_path)

        if not exclude_dir:
            if len(matching_excluded_paths) > 0:
                found_dirs.extend(calculate_dirs_to_upload(Path(local_dir, d), matching_excluded_paths))
            else:
                found_dirs.append(d)
    
    if found_exclude:
        # We found some dirs/files to exclude, so only return the ones we should upload
        found_dirs = [Path(local_dir, f) for f in found_dirs]
        return found_dirs
    else:
        # No exclusions found, we can upload the entire dir
        return [local_dir]

def get_remote_files(remote_dir):
    path_list = []
    output = cmd("mega-ls -Rl {}".format(remote_dir))
    
    current_dir = None
    for line in output.split("\n"):
        remote_path_match = remote_path_regex.match(line)
        if remote_path_match:
            # Add directory
            current_dir = posix_ensure_abs(PurePosixPath(remote_path_match.group(1)))
            path_list.append((current_dir, True))
        else:
            remote_file_match = remote_file_regex.match(line)
            if remote_file_match:
                # Only add this directory entry if it's not a directory
                attrs = remote_file_match.group(1)
                is_dir = attrs[0] == 'd'
                if not is_dir:
                    file_name = remote_file_match.group(6)
                    file_path = PurePosixPath(current_dir, file_name)
                    path_list.append((file_path, is_dir))
    
    return path_list

def remove_redundant_paths(paths):
    paths2 = []
    
    for path in paths:
        if len(paths2) == 0 or paths2[-1] not in path.parents:
            paths2.append(path)
    
    return paths2

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
