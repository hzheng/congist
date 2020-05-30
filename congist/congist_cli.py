#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line client for Congist.
"""

from os.path import expanduser, dirname, abspath, join
import sys
import traceback
from argparse import ArgumentParser, ArgumentTypeError
import yaml

from congist.Congist import Congist, Gist, ConfigurationError, ParameterError
from congist import __version__
from congist.utils import File


def _get_output(args):
    return open(expanduser(args.output), 'w') if args.output else sys.stdout


def _confirm(gist, action, is_file=False):
    reply = input("{} {} {}? (y/Y for yes) : "
                  .format(action, "file" if is_file else "gist", gist))
    if reply.lower() == 'y':
        return True

    print("skip", action)
    return False

# ============Command Argument Parse============
parser = ArgumentParser(description='Construct your gists')
subparsers = parser.add_subparsers(dest='subcommand')


def argument(*args, **kwargs):
    return (list(args), kwargs)


def subcommand(*args):
    def decorator(f):
        arg_parser = subparsers.add_parser(f.__name__, description=f.__doc__)
        for arg in args:
            arg_parser.add_argument(*arg[0], **arg[1])
        arg_parser.set_defaults(function=f)
    return decorator


def str2bool(val):
    if isinstance(val, bool):
        return val
    if val.upper() in ('T', 'Y', '1'):
        return True
    if val.upper() in ('F', 'N', '0'):
        return False
    raise ArgumentTypeError('Boolean value(T/F, Y/N, 1/0) expected')

sys_flags = (
    argument('-v', '--verbose', action='store_true',
             help='verbose output'),
    argument('-L', '--local-base', metavar='PATH',
             help='specify local base directory'))

filter_flags = (
    argument('-E', '--exact', action='store_true',
             help='enforce exact match'),
    argument('-S', '--case-sensitive', action='store_true',
             help='case sensitive when match'))

read_options = (
    argument('-o', '--output', metavar='PATH',
             help='specify output file'),
    argument('-l', '--local', action='store_true',
             help='get info from local instead of remote'))

write_options = (
    argument('-n', '--dry-run', action='store_true',
             help='dry run'),
    argument('--force', action='store_true',
             help='perform operations without confirmation'))

user_specifiers = (
    argument('-H', '--host', metavar='HOSTNAME',
             help='specify host name'),
    argument('-u', '--user', metavar='USERNAME',
             help='specify user'))

gist_specifiers = (
    *user_specifiers,
    argument('-p', '--public', nargs='?', metavar='BOOL',
             type=str2bool, default=None,
             help='specify public gists(1=public, 0=private)'),
    argument('-s', '--star', nargs='?', metavar='BOOL',
             type=str2bool, default=None,
             help='specify starred gists(1=starred, 0=unstarred)'),
    argument('-t', '--tags', nargs='+', metavar='TAG',
             help='specify gist tags'),
    argument('-d', '--description', metavar='DESCRIPTION-OR-PATTERN',
             help='specify gist description or pattern(regex)'))

gist_filters = (
    *filter_flags,
    argument('-i', '--id', nargs='+', metavar='GIST-ID',
             help='filter by gist IDs'),
    argument('-c', '--created', metavar='DATE', nargs='+',
             help='filter by created time'),
    argument('-m', '--modified', metavar='DATE', nargs='+',
             help='filter by modified time'))

file_specifiers = (
    *gist_specifiers,
    argument('-b', '--binary', action='store_true',
             help='specify binary file or include binary file in search'),
    argument('-f', '--file-name', metavar='NAME-OR-PATTERN',
             help='specify gist file name or pattern(regex)'))

file_filters = (
    *file_specifiers,
    *gist_filters,
    argument('-k', '--keyword', metavar='REGEX',
             help='filter by keyword'))

GIST_DEFAULT_FORMAT = "adp"


def format_help():
    help_msg = ""
    for k, val in Gist.format_map().items():
        help_msg += k + ": " + val + "\n"
    return help_msg + "empty: all of above, default: " + GIST_DEFAULT_FORMAT


@subcommand(*sys_flags, *read_options, *file_filters,
            argument('-F', '--format', nargs="?",
                     default=GIST_DEFAULT_FORMAT,
                     help="format of list (" + format_help() + ")"))
def lists(congist, args):
    """List all filtered gists with the given format."""
    output = _get_output(args)
    fmt = args.format
    try:
        for gist in congist.get_gists(**vars(args)):
            print(gist.get_info(fmt), file=output)
    except KeyError as e:
        raise ParameterError("unsupported format: {}\n{}"
                             .format(e, format_help()))


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


@subcommand(*sys_flags, *write_options, *file_filters,
            argument('-D', '--new-desc', metavar='DESC',
                     help='new gist description'),
            argument('-N', '--new-name', metavar='NAME',
                     help='new file name'),
            argument('-C', '--new-content', metavar='PATH',
                     nargs='?', default="",
                     help='new content path(stdin if absent)'))
def update(congist, args):
    """Update description and/or file name/content for filtered gists/files."""
    if args.new_desc:
        for gist in congist.get_gists(**vars(args)):
            if args.force or _confirm(gist, "update description"):
                gist.set_description(args.new_desc)
        return

    if args.new_name or args.new_content != '':
        content = None
        if args.new_content != '':
            content = File.read(args.new_content)
        for f in congist.get_files(**vars(args)):
            f.update(args.new_name, content)
    else:
        raise ParameterError("Please specify one of -D, -N, -C")


@subcommand(argument('new_tags', metavar='TAG', nargs='*',
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


@subcommand(argument('new_star', nargs='?', metavar='BOOL',
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


@subcommand(argument('file_paths', metavar='PATH', nargs='*',
                     help='file path(stdin if absent)'),
            *sys_flags, *write_options, *file_specifiers)
def create(congist, args):
    """Create gist from input files."""
    gist = congist.create_gist(args.file_paths, **vars(args))
    if args.verbose:
        print("created gist successfully" if gist
              else "failed to create gist")


@subcommand(*sys_flags, *write_options, *file_filters,
            argument('-F', '--is-file', action='store_true',
                     help="delete file instead of gist"))
def delete(congist, args):
    """Remove filtered gists or files."""
    options = vars(args)
    is_file = options.pop('is_file')
    for obj in congist.get_gists_or_files(is_file, **options):
        if args.force or _confirm(obj, "delete", is_file):
            obj.delete()


@subcommand()
def version():
    """Show the version of Congist."""
    print(__version__)


def main():
    # read command args
    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
        return

    # load system config
    cfg_file = join(dirname(abspath(__file__)), "../congist.yml")
    with open(cfg_file, 'r') as sys_file:
        sys_config = yaml.load(sys_file, yaml.SafeLoader)
        user_config_path = File.config_path(sys_config['user_cfg_path'])

        # load user config
        # TODO: if user_config_path does not exist, create a template
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
    except UnicodeError as ue:
        print("Please enable binary mode(-b):", ue)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print("Please report the bug:", e)
    finally:
        sys.exit(exit_code)
