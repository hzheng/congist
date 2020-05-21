# -*- coding: utf-8 -*-

"""
Congist is the core worker.
"""

import json
import re
import os
import sys
import string
import unicodedata
import importlib

from os.path import basename, expanduser, isdir, join

from congist.Gist import Gist

class Congist:
    LOCAL_BASE = 'local_base'
    METADATA_BASE = 'metadata_base'
    INDEX_FILE = 'index_file'
    DISABLE_FILTER = '_disable_filter'
    AGENTS = 'agents'
    REPOS = 'repos'
    USERNAME = 'username'
    HOST = 'host'
    USERS = 'users'
    USER = 'user'
    ACCESS_TOKEN = 'access_token'
    FILE_TYPE = 'file_type'
    FILE_NAME = 'file_name'
    DEFAULT_FILENAME = 'default_filename'
    FILE_EXT = 'file_extension'
    TEXT = 'text'
    ID = 'id'
    PUBLIC = 'public'
    STAR = 'star'
    DESC = 'description'
    TAGS = 'tags'
    DEFAULT_DESC = 'default_description'
    COMMIT = 'commit'
    COMMAND = 'command'
    MESSAGE = 'message'
    EXACT = 'exact'
    VERBOSE = 'verbose'
    DRY_RUN = 'dry_run'
    SSH = 'ssh'

    def __init__(self, config):
        self._local_dirs = {}
        self._host_agents = {}
        self.default_host = None
        self._default_users = {}
        try:
            agent_types = self._read_config(config)
            self._set_agents(agent_types)
            Gist.init(config)
        except KeyError as e:
            raise ConfigurationError(e)

    def _read_config(self, config):
        local_base = expanduser(config[self.LOCAL_BASE])
        if local_base[0] == '$':
            local_base = os.getenv(local_base[1:], os.getcwd())
        self._local_base = local_base
        self._metadata_base = join(local_base, config[self.METADATA_BASE])
        self._index_file = join(self._metadata_base, config[self.INDEX_FILE])
        file_type = config[self.FILE_TYPE]
        self._text_pattern = re.compile(file_type[self.TEXT])
        commit = config[self.COMMIT]
        self._commit_command = commit[self.COMMAND]
        self._commit_message = commit[self.MESSAGE]
        self._exact = config[self.EXACT]
        self._settings = config[self.REPOS]
        self._default_description = config[self.DEFAULT_DESC]
        self._default_filename = config[self.DEFAULT_FILENAME]
        if not self._settings:
            raise ConfigurationError(self.REPOS + " has empty setting")

        return config[self.AGENTS]

    def _set_agents(self, agent_types):
        for host, settings in self._settings.items():
            if host not in agent_types:
                raise ConfigurationError("Host " + host + " not yet supported")

            agents = self._host_agents[host] = {}
            if not self.default_host:
                self._default_host = host
            for user in settings[self.USERS]:
                username = user[self.USERNAME]
                if host not in self._default_users:
                    self._default_users[host] = username
                user_local_base = self.get_local_host_base(host, username)
                os.makedirs(user_local_base, exist_ok=True)
                self.set_local_dir(host, username, user_local_base)
                # dynamically load agent class
                agent_module, agent_class = agent_types[host].split('.')
                module = importlib.import_module(agent_module)
                agent_type = getattr(module, agent_class)
                agents[username] = agent_type(user[self.ACCESS_TOKEN])
            
            if host not in self._default_users:
                raise ConfigurationError("Please set at least one user at " + host)

    @property
    def hosts(self):
        return self._host_agents.keys()

    @property
    def local_base(self):
        return self._local_base

    @property
    def metadata_base(self):
        return self._metadata_base

    def get_local_host_base(self, host, user):
        return join(self.local_base, host, user)

    def set_local_dir(self, host, user, path):
        self._local_dirs[host + "." + user] = path

    def get_local_dir(self, host, user):
        return self._local_dirs[host + "." + user]

    def _get_local_parent(self, gist):
        return self.get_local_dir(gist.host, gist.user)

    def get_agents(self, host):
        try:
            return self._host_agents[host]
        except KeyError:
            raise ParameterError("Host " + host + " not yet supported")

    def get_users(self, host):
        return self.get_agents(host).keys()

    def _get_agent(self, agents, user, exact):
        if exact:
            if user not in agents:
                raise ParameterError("User " + user + " not found")
        else:
            matched_users = [u for u in agents.keys() if user in u ]
            if len(matched_users) == 0:
                raise ParameterError("No fuzzy matched user found for " + user)
            if len(matched_users) > 1:
                raise ParameterError("More than 1 user fuzzy match for " + user)
            user = matched_users[0]

        return agents[user]

    def get_gists(self, **args):
        host = args[self.HOST]
        hosts = self.hosts if host is None else [host]
        for host in hosts:
            agents = self.get_agents(host)
            user = args[self.USER]
            users = [user] if user else self.get_users(host)
            for user in users:
                if args[self.VERBOSE]:
                    print("user", user) # TODO: change to callback
                agent = self._get_agent(agents, user, self._exact)
                for g in agent.get_gists():
                    gist = Gist(g, host)
                    if self._filter_gist(gist, **args):
                        yield gist

    def _filter_gist(self, gist, **args):
        if self.DISABLE_FILTER in args:
            return True

        gist_id = args[self.ID]
        if gist_id:
            if self._exact:
                if  gist.id not in gist_id:
                    return False
            else:
                if all(gid not in gist.id for gid in gist_id):
                    return False
        desc = args[self.DESC]
        if desc and (gist.description is None or desc not in gist.description):
            return False
        tags = args[self.TAGS]
        if tags and not gist.has_tags(tags):
            return False
        public = args[self.PUBLIC]
        if (public == 0 and gist.public) or (public == 1 and not gist.public):
            return False
        star = args[self.STAR]
        if star and not gist.starred:
            return False
        return True

    def get_infos(self, **args):
        for gist in self.get_gists(**args):
            yield gist.get_info() 

    def generate_full_index(self, **args):
        args = args.copy()
        args.update({self.USER: None, self.DISABLE_FILTER: True})
        for host in self.hosts:
            args.update({self.HOST: host})
            index_file = self._index_file.format(host=host)
            if args[self.VERBOSE]:
                print("generating index file:", index_file)
            if not args[self.DRY_RUN]:
                with open(index_file, 'w') as f:
                    self.generate_index(f, **args)

    def generate_index(self, file, **args):
        host = args[self.HOST]
        if host is None:
            host = self._default_host
        index = { user: [] for user in self.get_users(host) }
        for gist in self.get_gists(**args):
            index[gist.user].append(gist.get_info())
        json_output = json.dumps(index, indent=4)
        print(json_output, file=file)

    def get_files(self, **args):
        for gist in self.get_gists(**args):
            for name, file in gist.files.items():
                if self._match_filename(name.lower(), **args):
                    yield name, file.content

    def _match_filename(self, filename, **args):
        file_ext = args[self.FILE_EXT]
        if file_ext:
            extensions = tuple(file_ext.split(','))
            if not filename.endswith(extensions):
                return False
        elif not self._text_pattern.match(filename):
            return False
        return True

    def sync_gists(self, **args):
        self.download_gists(**args)
        self.upload_gists(**args)

    def download_gists(self, **args):
        for gist in self.get_gists(**args):
            local_parent = self._get_local_parent(gist)
            local_dir = join(local_parent, self._dir_name(gist))
            if isdir(local_dir):
                self._pull_gists(local_dir, **args)
            else:
                self._clone_gists(gist, local_dir, **args)

    VALID_FILENAME_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
    def _clean_name(self, name):
        cleaned = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore')
        return ''.join(chr(c) for c in cleaned if chr(c) in self.VALID_FILENAME_CHARS)

    def _dir_name(self, gist):
        name = self._clean_name(gist.title).replace(' ', '_')
        return name + "_" + gist.id[:6]

    def _clone_gists(self, gist, local_dir, **args):
        if args[self.SSH]:
            gist_url = "git@" + gist.pull_url.replace('/', ':')[8:]
        else:
            gist_url = gist.pull_url
        cmd = "git clone {verbose} {url} {local_dir}".format(
            local_dir=local_dir, verbose=("" if args[self.VERBOSE] else " -q"), url=gist_url)
        if args[self.DRY_RUN]:
            print(cmd)
        else:
            os.system(cmd)

    def _pull_gists(self, local_dir, **args):
        #TODO: put rebase option in arguments or setting
        cmd = "cd {}; git pull {}".format(local_dir, "" if args[self.VERBOSE] else " -q")
        if args[self.DRY_RUN]:
            print(cmd)
        else:
            os.system(cmd)

    def upload_gists(self, **args):
        for gist in self.get_gists(**args):
            self._upload_gists(gist, **args)

    def _upload_gists(self, gist, **args):
        local_dir = self.get_local_host_base(gist.host, gist.user)
        if not isdir(local_dir):
            return

        for subdir in os.listdir(local_dir):
            subdir = join(local_dir, subdir)
            if not isdir(subdir):
                continue
            cmd = ("cd {subdir} &&" + self._commit_command).format(
                subdir=subdir, comment=self._commit_message,
                verbose=("" if args[self.VERBOSE] else "-q"))
            if args[self.DRY_RUN]:
                print(cmd)
            else:
                os.system(cmd)

    def create_gists(self, paths, **args):
        host = args[self.HOST]
        if host is None:
            host = self._default_host
        agents = self.get_agents(host)
        user = args[self.USER]
        if user is None:
            user = self._default_users[host] # at least 1
        agent = self._get_agent(agents, user, self._exact)
        public = args[self.PUBLIC] or False
        desc = args[self.DESC] or self._default_description
        files = {}
        if paths:
            for path in paths:
                self._set_content(files, expanduser(path))
        else:
            self._set_content_from_stdin(files, **args)
        agent.create_gist(files, public, desc)

    def _set_content(self, files, path):
        with open(path, 'r') as f: # TODO: use binary mode depends on file type
            content = f.read()
            files[basename(path)] = content

    def _set_content_from_stdin(self, files, **args):
        filename = args[self.FILE_NAME] or self._default_filename
        content = sys.stdin.read()
        files[filename] = content

class ClientError(Exception):
    """Client-side error"""
    pass


class ConfigurationError(ClientError):
    """Configuration error"""
    pass


class ParameterError(ClientError):
    """Parameter error"""
    pass
