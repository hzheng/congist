#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line client for Congist.
"""

from os.path import expanduser, dirname, abspath, join
import sys
import traceback
import yaml
import argparse
import json

from congist.Congist import Congist, ConfigurationError, ParameterError

def list_gists(congist, args):
    output = _get_output(args)
    for gist in congist.get_gists(**vars(args)):
        print(gist, file=output)

def index_gists(congist, args):
    index = congist.get_infos(**vars(args))
    json_output = json.dumps(list(index), indent=4)
    print(json_output, file= _get_output(args))

def read_gists(congist, args):
    output = _get_output(args)
    for filename, content in congist.get_files(**vars(args)):
        if args.verbose:
            print("====={}======".format(filename))
        print(content, file=output)

def _get_output(args):
    if args.output:
        return open(expanduser(args.output), 'w')
    return sys.stdout

def refresh_gists(congist, args):
    congist.sync_gists(**vars(args))

def download_gists(congist, args):
    congist.download_gists(**vars(args))

def upload_gists(congist, args):
    congist.upload_gists(**vars(args))

def create_gists(congist, args):
    congist.create_gists(args.create, **vars(args))

def delete_gists(congist, args):
    for gist in congist.get_gists(**vars(args)):
        if args.force or _confirm(gist, "delete"):
            gist.delete()

def desc_gists(congist, args):
    for gist in congist.get_gists(**vars(args)):
        if not args.desc:
            print(gist.description)
        elif args.force or _confirm(gist, "set description"):
            gist.set_description(' '.join(args.desc))

def tag_gists(congist, args):
    for gist in congist.get_gists(**vars(args)):
        if not args.set_tags:
            print(gist.tags)
        elif args.force or _confirm(gist, "set tag"):
            gist.set_tags(args.set_tags)

def toggle_star_gists(congist, args):
    for gist in congist.get_gists(**vars(args)):
        if args.force or _confirm(gist, "toggle star"):
            gist.toggle_starred()

def _confirm(gist, action):
    reply = input("{} gist {}? (y/Y for yes) : ".format(action, gist))
    if reply.lower() == 'y':
        return True
    else:
        print("skip", action)
        return False

def parse_args():
    parser = argparse.ArgumentParser(description='Construct your gists')
    parser.add_argument('-l', '--list', action='store_true',
                       help='list gists')
    parser.add_argument('-I', '--index', action='store_true',
                       help='print index of gists')
    parser.add_argument('-i', '--id', nargs='+', 
                       help='specify gist id')
    parser.add_argument('-d', '--description',
                       help='gist description(used in gist filter/creation)')
    parser.add_argument('-D', '--set-desc', nargs='*',
                       help='gist description(used in gist description getter/setter)')
    parser.add_argument('-t', '--tags', nargs='+',
                       help='filter by gist tags')
    parser.add_argument('-T', '--set-tags', nargs='*',
                       help='get/set tags for gists')
    parser.add_argument('-p', '--public', nargs='?', const=0, type=int,
                       help='specify public gist(empty or 0:private 1:public)')
    parser.add_argument('-c', '--create', nargs='*',
                       help='create gists from input files')
    parser.add_argument('--delete', action='store_true',
                       help='delete gists')
    parser.add_argument('-f', '--file-name',
                       help='specify file name')
    parser.add_argument('--force', action='store_true',
                       help='perform operations without confirmation')
    parser.add_argument('-o', '--output',
                       help='specify output file')
    parser.add_argument('-e', '--file-extension',
                       help='specify the file name suffix(comma separated)')
    parser.add_argument('-s', '--star', action='store_true',
                       help='show only starred gists')
    parser.add_argument('-S', '--toggle-star', action='store_true',
                       help='toggle star of gists')
    parser.add_argument('-r', '--read', action='store_true',
                       help='read text type or specified type gists')
    parser.add_argument('-R', '--refresh', action='store_true',
                       help='refresh/synchronize gists')
    parser.add_argument('--download', action='store_true',
                       help='download gists')
    parser.add_argument('--upload', action='store_true',
                       help='upload gists')
    parser.add_argument('-C', '--local-base',
                       help='change local base directory')
    parser.add_argument('-H', '--host',
                       help='specify host')
    parser.add_argument('-E', '--exact', nargs='?', const=True, 
                       help='enforce exact match')
    parser.add_argument('--ssh', action='store_true',
                       help='use SSH instead HTTPS')
    parser.add_argument('-u', '--user',
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
    with open(cfg_file, 'r') as sys_file:
        sys_config = yaml.load(sys_file, yaml.SafeLoader)
        user_config_path = expanduser(sys_config['user_cfg_path'])
    
        # load user config
        # TODO: if user_config_path does not exist, prompt and create a template
        with open(user_config_path, 'r') as user_file:
            # override order: sys config -> user config -> command args
            user_config = yaml.load(user_file, yaml.SafeLoader)
            config = {**sys_config, **user_config}
            for key, value in vars(args).items():
                if value is not None:
                    config[key] = value

            congist = Congist(config)
            if args.list:
                list_gists(congist, args)
            elif args.index:
                index_gists(congist, args)
            elif args.read:
                read_gists(congist, args)
            elif args.refresh:
                refresh_gists(congist, args)
            elif args.download:
                download_gists(congist, args)
            elif args.upload:
                upload_gists(congist, args)
            elif args.create is not None:
                create_gists(congist, args)
            elif args.set_desc is not None:
                desc_gists(congist, args)
            elif args.set_tags is not None:
                tag_gists(congist, args)
            elif args.delete:
                delete_gists(congist, args)
            elif args.toggle_star:
                toggle_star_gists(congist, args)
            else:
                raise ParameterError("No action specified")

if __name__ == '__main__':
    exit_code = 1
    try:
        main()
        exit_code = 0
    except (ConfigurationError, yaml.YAMLError) as ce:
        print("Please fix the configuration setting:", ce)
    except ParameterError as pe:
        print("Please fix the parameter:", pe)
    except OSError as oe:
        print("Please fix the OS-related problem:", oe)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print("Please report the bug:", e)
    finally:
        sys.exit(exit_code)
