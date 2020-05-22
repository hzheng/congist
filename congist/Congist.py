# -*- coding: utf-8 -*-

"""
Congist is the core worker.
"""

import json
import re
import os
import sys
import importlib

from os.path import basename, expanduser, isdir, join

from congist.Gist import GistUser, Gist
from congist.LocalAgent import LocalAgent
from congist.LocalGist import LocalGist

class Congist:
    LOCAL_BASE = 'local_base'
    METADATA_BASE = 'metadata_base'
    INDEX_FILE = 'index_file'
    DISABLE_FILTER = '_disable_filter'
    AGENTS = 'agents'
    LOCAL = 'local'
    REPOS = 'repos'
    HOST = 'host'
    USERS = 'users'
    USER = 'user'
    FILE_TYPE = 'file_type'
    FILE_NAME = 'file_name'
    DEFAULT_FILENAME = 'default_filename'
    FILE_EXT = 'file_extension'
    BINARY = 'binary'
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
        self._local_agents = {}
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

            host_agents = self._host_agents[host] = {}
            local_agents = self._local_agents[host] = {}
            index_file = self._index_file.format(host=host)
            if not self.default_host:
                self._default_host = host
            for user in settings[self.USERS]:
                gist_user = GistUser(**user)
                username = gist_user.username
                if host not in self._default_users:
                    self._default_users[host] = username
                user_local_base = self.get_local_host_base(host, username)
                os.makedirs(user_local_base, exist_ok=True)
                self.set_local_dir(host, username, user_local_base)
                # dynamically load agent class
                agent_module, agent_class = agent_types[host].split('.')
                module = importlib.import_module(agent_module)
                agent_type = getattr(module, agent_class)
                agent = agent_type(gist_user=gist_user)
                host_agents[username] = agent
                local_agents[username] = LocalAgent(remote_agent=agent,
                                                    local_base=user_local_base,
                                                    index_file=index_file)
            
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

    def get_local_host_base(self, host, username):
        return join(self.local_base, host, username)

    def set_local_dir(self, host, username, path):
        self._local_dirs[host + "." + username] = path

    def get_local_dir(self, host, username):
        return self._local_dirs[host + "." + username]

    def _get_local_parent(self, gist):
        return self.get_local_dir(gist.host, gist.username)

    def get_agents(self, host, local=False):
        try:
            return (self._local_agents if local else self._host_agents)[host]
        except KeyError:
            raise ParameterError("Host " + host + " not yet supported")

    def get_users(self, host):
        return self.get_agents(host).keys()

    def _get_agent(self, agents, username, exact):
        if exact:
            if username not in agents:
                raise ParameterError("Username " + username + " not found")
        else:
            matched_users = [u for u in agents.keys() if username in u ]
            if len(matched_users) == 0:
                raise ParameterError("No fuzzy matched username found for " + username)
            if len(matched_users) > 1:
                raise ParameterError("More than 1 username fuzzy match for " + username)
            username = matched_users[0]

        return agents[username]

    def get_gists(self, **args):
        host = args[self.HOST]
        hosts = self.hosts if host is None else [host]
        for host in hosts:
            agents = self.get_agents(host, args[self.LOCAL])
            username = args[self.USER]
            users = [username] if username else self.get_users(host)
            for u in users:
                if args[self.VERBOSE]:
                    print("username", u) # TODO: change to callback
                agent = self._get_agent(agents, u, self._exact)
                for gist in agent.get_gists():
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
        index = {u: [] for u in self.get_users(host)}
        for gist in self.get_gists(**args):
            index[gist.username].append(gist.get_info())
        json_output = json.dumps(index, indent=4)
        print(json_output, file=file)

    def get_files(self, **args):
        for gist in self.get_gists(**args):
            for f in gist.file_entries:
                if self._match_filename(f.name, **args):
                    yield f

    def _match_filename(self, filename, **args):
        filename = filename.lower()
        name = args[self.FILE_NAME]
        if name and name.lower() not in filename:
            return False
        file_ext = args[self.FILE_EXT]
        if file_ext:
            extensions = tuple(ext.lower() for ext in file_ext.split(','))
            if not filename.endswith(extensions):
                return False
        elif not args[self.BINARY] and not self._text_pattern.match(filename):
            return False
        return True

    def sync_gists(self, **args):
        self.download_gists(**args)
        self.upload_gists(**args)

    def download_gists(self, **args):
        for gist in self.get_gists(**args):
            local_parent = self._get_local_parent(gist)
            local_dir = join(local_parent, LocalGist.dir_name(gist))
            if isdir(local_dir):
                self._pull_gists(local_dir, **args)
            else:
                self._clone_gists(gist, local_dir, **args)

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
        local_dir = self.get_local_host_base(gist.host, gist.username)
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
        username = args[self.USER]
        if username is None:
            username = self._default_users[host] # at least 1
        agent = self._get_agent(agents, username, self._exact)
        public = args[self.PUBLIC] or False
        desc = args[self.DESC] or self._default_description
        files = {}
        if paths:
            for path in paths:
                self._set_content(files, expanduser(path))
        else:
            self._set_content_from_stdin(files, **args)
        return agent.create_gist(files, public, desc)

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
