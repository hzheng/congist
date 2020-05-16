#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line client for Congist.
"""

from os.path import expanduser
import sys
import argparse
import json

from congist.Congist import Congist

def list(congist, args):
    for user in congist.users:
        if args.user is not None and args.user != user:
            continue

        if args.verbose:
            print("Listing gists for " + user)
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

def download(congist, args):
    for user in congist.users:
        if args.user is not None and args.user != user:
            continue

        if args.verbose:
            print("Downloading gists for " + user)
        for gist in congist.get_gists(user):
            congist.download_gist(gist, **vars(args))

def upload(congist, args):
    for user in congist.users:
        if args.user is not None and args.user != user:
            continue

        if args.verbose:
            print("Uploading gists for " + user)
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
    config_path = expanduser("~/.congist")
    # TODO: if config_path not exist, prompt and create a template
    with open(config_path) as config_json:
        config = json.load(config_json)
        if args.local_base:
            config[Congist.LOCAL_BASE] = args.local_base
        congist = Congist(config)
        if args.list:
            list(congist, args)
        elif args.index:
            index(congist, args)
        elif args.download:
            download(congist, args)
        elif args.upload:
            upload(congist, args)
        else:
            print("add gist from input") #TODO


if __name__ == '__main__':
    sys.exit(main())
