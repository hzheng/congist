#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line client for Congist.
"""

from os.path import expanduser, dirname, abspath, join
import sys
import traceback
import yaml
from argparse import ArgumentParser, ArgumentTypeError
import json

from congist.Congist import Congist, Gist, ConfigurationError, ParameterError


def _get_output(args):
    return open(expanduser(args.output), 'w') if args.output else sys.stdout


def _confirm(gist, action):
    reply = input("{} gist {}? (y/Y for yes) : ".format(action, gist))
    if reply.lower() == 'y':
        return True
    else:
        print("skip", action)
        return False

#############Command Argument Parse#############
parser = ArgumentParser(description='Construct your gists')
subparsers = parser.add_subparsers(dest='subcommand')

def argument(*args, **kwargs):
    return (list(args), kwargs)

def subcommand(*args):
    def decorator(f):
        parser = subparsers.add_parser(f.__name__, description=f.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(function=f)
    return decorator

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.upper() in ('T', 'Y', '1'):
        return True
    elif v.upper() in ('F', 'N', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value(T/F, Y/N, 1/0) expected')

sys_flags = (
    argument('-v', '--verbose', action='store_true',
             help='verbose output'),
    argument('-L', '--local-base', metavar='path',
             help='specify local base directory'))

filter_flags = (
    argument('-E', '--exact', action='store_true',
             help='enforce exact match'),
    argument('-S', '--case-sensitive', action='store_true',
             help='case sensitive when match'))

read_options = (
    argument('-o', '--output', metavar='path',
             help='specify output file'),
    argument('-l', '--local', action='store_true',
             help='get info from local instead of remote'))

write_options = (
    argument('-n', '--dry-run', action='store_true',
             help='dry run'),
    argument('--force', action='store_true',
             help='perform operations without confirmation'))

user_specifiers = (
    argument('-H', '--host', metavar='hostname',
             help='specify host name'),
    argument('-u', '--user', metavar='user',
             help='specify user'))

gist_specifiers = (
    *user_specifiers,
    argument('-p', '--public', nargs='?', metavar='bool', 
             type=str2bool, default=None,
             help='specify public gists(1=public, 0=private)'),
    argument('-s', '--star', nargs='?', metavar='bool', 
             type=str2bool, default=None,
             help='specify starred gists(1=starred, 0=unstarred)'),
    argument('-t', '--tags', nargs='+', metavar='tag',
             help='specify gist tags'),
    argument('-d', '--description', metavar='description-or-pattern',
             help='specify gist description or pattern(regex)'))

gist_filters = (
    *filter_flags,
    argument('-i', '--id', nargs='+', metavar='gist-id',
             help='filter by gist IDs'),
    argument('-c', '--created', metavar='created-date', nargs='+', 
             help='filter by created time'),
    argument('-m', '--modified', metavar='modified-date', nargs='+',
             help='filter by modified time'))

file_specifiers = (
    *gist_specifiers,
    argument('-f', '--file-name', metavar='name-or-pattern',
             help='specify gist file name or pattern(regex)'))

file_filters = (
    *file_specifiers,
    *gist_filters,
    argument('-k', '--keyword', metavar='regex',
             help='filter by keyword'),
    argument('-b', '--binary', action='store_true',
                help='including binary file(default: presetted text file extensions only)'))

gist_default_format = "adp"

def format_help():
    help = ""
    for k, v in Gist.format_map().items():
        help += k + ": " + v + "\n"
    return help + "empty: all of above, default: " + gist_default_format

@subcommand(*sys_flags, *read_options, *file_filters,
            argument('-F', '--format', metavar='format', nargs="?",
                     default=gist_default_format,
                     help="format of list (" + format_help() + ")"))
def ls(congist, args):
    """List all filtered gists with the given format."""
    output = _get_output(args)
    format = args.format
    try:
        for gist in congist.get_gists(**vars(args)):
            print(gist.get_info(format), file=output)
    except KeyError as e:
        raise ParameterError("unsupported format: {}\n{}".format(e, format_help()))

@subcommand(*sys_flags, *read_options, *file_filters)
def info(congist, args):
    """Print all filtered gists' info in JSON format."""
    congist.generate_index(_get_output(args), **vars(args))

@subcommand(*sys_flags)
def index(congist, args):
    """Dump all gists' info in JSON format to an index file."""
    congist.generate_full_index(**vars(args))

@subcommand(*sys_flags, *write_options, *file_filters,
            argument('-D', '--download', action='store_true',
                     help='download gists only'),
            argument('-U', '--upload', action='store_true',
                     help='upload gists only'),
            argument('--ssh', action='store_true',
                     help='clone via SSH instead HTTPS'))
def sync(congist, args):
    """Refresh/synchronize gists."""
    if args.download:
        congist.download_gists(**vars(args))
    elif args.upload:
        congist.upload_gists(**vars(args))
    else:
        congist.sync_gists(**vars(args))
        if not args.dry_run:
            congist.generate_full_index(**vars(args))

@subcommand(*sys_flags, *read_options, *file_filters)
def read(congist, args):
    """Read filtered gists."""
    output = _get_output(args)
    for f in congist.get_files(**vars(args)):
        content = f.content
        if args.verbose:
            print("====={}======".format(f.name))
        if isinstance(content, str):
            output.write(content)
        else:
            output.buffer.write(content)

@subcommand(argument('new_desc', metavar='desc',
                     help='new gist description'),
            *sys_flags, *write_options, *file_filters)
def desc(congist, args):
    """Set description for filtered gists."""
    for gist in congist.get_gists(**vars(args)):
        if args.force or _confirm(gist, "set description"):
            gist.set_description(args.new_desc)

@subcommand(argument('new_tags', metavar='tag', nargs='*',
                     help='new gist tags'),
            *sys_flags, *read_options, *write_options, *file_filters)
def tag(congist, args):
    """Set/get tags for filtered gists"""
    if args.new_tags:
        for gist in congist.get_gists(**vars(args)):
            if args.force or _confirm(gist, "set tag"):
                gist.set_tags(args.new_tags)
    else:
        tags = congist.list_tags(**vars(args))
        print(", ".join(tags), file=_get_output(args))
        

@subcommand(argument('new_star', nargs='?', metavar='bool',
                     type=str2bool, default=None,
                     help='1: star, 0: unstar, empty: toggle star'),
            *sys_flags, *write_options, *file_filters)
def star(congist, args):
    """Set or toggle star for filtered gists."""
    for gist in congist.get_gists(**vars(args)):
        if args.new_star is None:
            if args.force or _confirm(gist, "toggle star"):
                gist.toggle_starred()
        elif args.force or _confirm(gist, "set star"):
            gist.set_starred(args.new_star)
 
@subcommand(argument('file_paths', metavar='file-path', nargs='*',
                    help='file path(stdin if absent)'),
            *sys_flags, *write_options, *file_specifiers)
def new(congist, args):
    """Create gists from input files."""
    congist.create_gists(args.file_paths, **vars(args))

@subcommand(*sys_flags, *write_options, *file_filters)
def rm(congist, args):
    """Remove filtered gists."""
    for gist in congist.get_gists(**vars(args)):
        if args.force or _confirm(gist, "delete"):
            gist.delete()


def main(argv=None):
    # read command args
    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
        return
    
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

            args.function(Congist(config), args)

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
