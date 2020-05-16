#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line client for Congist.
"""

from os.path import expanduser, dirname, abspath, join
import sys
import yaml
import argparse
import json

from congist.Congist import Congist

def list(congist, args):
    for user in congist.users:
        if args.user is not None and args.user != user:
            continue

        if args.verbose:
            print("Listing gists for", user)
        for gist in congist.get_gists(user):
            print(gist)

def index(congist, args):
    if args.user is None:
        index = congist.get_index()
    else:
        index = congist.get_user_index(args.user)
    json_output = json.dumps(index, indent=4)
    if args.output:
        with open(args.output, "w") as f:
            f.write(json_output)
    else:
        print(json_output)

def read(congist, args):
    output = sys.stdout
    if args.output:
        output = open(args.output, "w")
    for filename, content in congist.read_file(**vars(args)):
        if args.verbose:
            print("====={}======".format(filename))
        print(content, file=output)

def download(congist, args):
    for user in congist.users:
        if args.user is not None and args.user != user:
            continue

        if args.verbose:
            print("Downloading gists for", user)
        for gist in congist.get_gists(user):
            congist.download_gist(gist, **vars(args))

def upload(congist, args):
    for user in congist.users:
        if args.user is not None and args.user != user:
            continue

        if args.verbose:
            print("Uploading gists for", user)
        congist.upload_gist(user, **vars(args))

def parse_args():
    parser = argparse.ArgumentParser(description='Construct your gists')
    parser.add_argument('-l', '--list', action='store_true',
                       help='list gists')
    parser.add_argument('-i', '--index', action='store_true',
                       help='print index of gists')
    parser.add_argument('-o', '--output',
                       help='specify output file')
    parser.add_argument('-d', '--download', action='store_true',
                       help='download gists')
    parser.add_argument('-e', '--file-extension',
                       help='specify the file extensions(comma separated)')
    parser.add_argument('-r', '--read', action='store_true',
                       help='read gists')
    parser.add_argument('-u', '--upload', action='store_true',
                       help='upload gists')
    parser.add_argument('-C', '--local-base',
                       help='change local base directory')
    parser.add_argument('-H', '--host',
                       help='specify host')
    parser.add_argument('-S', '--ssh', action='store_true',
                       help='use SSH instead HTTPS')
    parser.add_argument('-U', '--user',
                       help='specify user')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='verbose output')
    parser.add_argument('-n', '--dry-run', action='store_true',
                       help='dry run')
    return parser.parse_args()

def main(argv=None):
    args = parse_args()
    # load system config
    cfg_file = join(dirname(abspath(__file__)), "../congist.yml")
    with open(cfg_file, "r") as sys_file:
        sys_config = yaml.load(sys_file, yaml.SafeLoader)
        user_config_path = expanduser(sys_config['user_cfg_path'])
    
        # load user config
        # TODO: if user_config_path does not exist, prompt and create a template
        with open(user_config_path, "r") as user_file:
            # override order: sys config -> user config -> command args
            user_config = yaml.load(user_file, yaml.SafeLoader)
            config = {**sys_config, **user_config}
            for key, value in vars(args).items():
                if value is not None:
                    config[key] = value

            congist = Congist(config)
            if args.list:
                list(congist, args)
            elif args.index:
                index(congist, args)
            elif args.read:
                read(congist, args)
            elif args.download:
                download(congist, args)
            elif args.upload:
                upload(congist, args)
            else:
                print("add gist from input") #TODO


if __name__ == '__main__':
    sys.exit(main())
