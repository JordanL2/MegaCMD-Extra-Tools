#!/usr/bin/python3

import os
import re
import subprocess
import sys


remote_path_regex = re.compile(r'(/.+):')
remote_file_regex = re.compile(r'(.{4})\s+([\-0-9]+)\s+([\-0-9]+)\s+(\d\d\w\w\w\d\d\d\d)\s+(\d\d:\d\d:\d\d)\s+(.+)')


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
    excludes = [[ee for ee in e.split('/') if ee != ''] for e in excludes]
    out("Syncing from {} to {}".format(local_dir, remote_dir))
    
    # Make remote dir
    cmd("mega-mkdir -p {}".format(remote_dir), ignore_errors=True)
    
    # Delete dirs/files in remote that don't exist in local
    remote_files = get_remote_files(remote_dir)
    to_delete = []
    for f in remote_files:
        file_name = f[0]
        local_file_path = ('/' + parent_dir(local_dir) + file_name).replace('//', '/')
        is_dir = f[1]
        if is_dir:
            if not os.path.isdir(local_file_path):
                to_delete.append(file_name)
        else:
            if not os.path.isfile(local_file_path):
                to_delete.append(file_name)
    
    to_delete = remove_redundant_paths(to_delete)
    for f in to_delete:
        out("Delete from remote: {}".format(f))
        cmd("mega-rm -rf \"{}\"".format(f))
    
    # Upload new/modified files to remote
    dirs_to_upload = calculate_dirs_to_upload(local_dir, excludes)
    for d in dirs_to_upload:
        remote_parent_dir = parent_dir(remote_dir + '/' + d[len(local_dir):])
        out("Upload {} into {}".format(d, remote_parent_dir))
        cmd("mega-put -c \"{}\" \"{}\"".format(d, remote_parent_dir))

def calculate_dirs_to_upload(local_dir, excludes, root=None):
    if len(excludes) == 0:
        return [local_dir]

    with_root = local_dir
    if root is not None:
        with_root = root + '/' + local_dir
    
    found_exclude = False
    found_dirs = []
    dirs = os.listdir(with_root)
    for d in dirs:
        matching_excludes = []
        exclude_dir = False
        for e in excludes:
            if e[0] == d:
                # This dir matches a path we should exclude
                found_exclude = True
                if len(e) == 1:
                    # This dir *entirely* matches the exclude, so we exclude it
                    exclude_dir = True
                else:
                    # This dir *partially* matches the exclude, so we need to work out
                    # what dirs/files inside it we can upload
                    matching_excludes.append(e[1:])
        
        if not exclude_dir:
            if len(matching_excludes) > 0:
                found_dirs.extend(calculate_dirs_to_upload(d, matching_excludes, with_root))
            else:
                found_dirs.append(d)
    
    if found_exclude:
        # We found some dirs/files to exclude, so only return the ones we should upload
        found_dirs = ["{}/{}".format(local_dir, f) for f in found_dirs]
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
            current_dir = remote_path_match.group(1)
            path_list.append((current_dir, True))
        else:
            remote_file_match = remote_file_regex.match(line)
            if remote_file_match:
                attrs = remote_file_match.group(1)
                file_name = remote_file_match.group(6)
                path_list.append((current_dir + '/' + file_name, attrs[0] == 'd'))
    
    return path_list

def remove_redundant_paths(paths):
    paths2 = set()
    
    for path in paths:
        ps = [p for p in path.split('/')]
        if len(ps) == 1:
            paths2.add(path)
        else:
            for i in range(0, len(ps) - 1):
                path_start = '/'.join(ps[0 : i + 1])
                if path_start in paths2:
                    break
            else:
                paths2.add(path)
    
    return paths2

def parent_dir(dir_name):
    ds = [d for d in dir_name.split('/') if d != '']
    if len(ds) <= 1:
        return '/'
    return '/'.join(ds[0:-1])

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
