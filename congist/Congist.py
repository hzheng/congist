# -*- coding: utf-8 -*-

"""
Congist is the core worker.
"""

import re
import os
import sys

from os.path import basename, expanduser, isdir, join

from github import Github, InputFileContent

from congist.Gist import Gist

class Congist:
    LOCAL_BASE = 'local_base'
    REPOS = 'repos'
    USERNAME = 'username'
    HOST = 'host'
    USERS = 'users'
    USER = 'user'
    ACCESS_TOKEN = 'access_token'
    GITHUB = 'github'
    FILE_TYPE = 'file_type'
    FILE_NAME = 'file_name'
    DEFAULT_FILENAME = 'default_filename'
    FILE_EXT = 'file_extension'
    TEXT = 'text'
    ID = 'id'
    PUBLIC = 'public'
    STAR = 'star'
    DESC = 'description'
    MATCH_TAGS = 'match_tags'
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
            self._read_config(config)
            Gist.init(config)
        except KeyError as e:
            raise ConfigurationError(e)

    def _read_config(self, config):
        local_base = expanduser(config[self.LOCAL_BASE])
        if local_base[0] == '$':
            local_base = os.getenv(local_base[1:], os.getcwd())
        self._local_base = local_base
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

        for host, settings in self._settings.items():
            agent = self._host_agents[host] = {}
            if not self.default_host:
                self._default_host = host
            if host == self.GITHUB:
                for user in settings[self.USERS]:
                    username = user[self.USERNAME]
                    if host not in self._default_users:
                        self._default_users[host] = username
                    user_local_base = self.get_local_host_base(host, username)
                    os.makedirs(user_local_base, exist_ok=True)
                    self.set_local_dir(host, username, user_local_base)
                    agent[username] = Github(user[self.ACCESS_TOKEN])
            else:
                raise ConfigurationError("Host " + host + " not yet supported")
            
            if host not in self._default_users:
                raise ConfigurationError("Please set at least one user at " + host)

    @property
    def hosts(self):
        return self._host_agents.keys()

    @property
    def local_base(self):
        return self._local_base

    def get_local_host_base(self, host, user):
        return join(self.local_base, host, user)

    def set_local_dir(self, host, user, path):
        self._local_dirs[host + "." + user] = path

    def get_local_dir(self, host, user):
        return self._local_dirs[host + "." + user]

    def _get_local_parent(self, gist):
        return self.get_local_dir(gist.host, gist.user)

    def get_agent(self, host):
        try:
            return self._host_agents[host]
        except KeyError:
            raise ParameterError("Host " + host + " not yet supported")

    def get_users(self, host):
        return self.get_agent(host).keys()

    def _get_user(self, agent, user, exact):
        if exact:
            if user not in agent:
                raise ParameterError("User " + user + " not found")
        else:
            matched_users = [u for u in agent.keys() if user in u ]
            if len(matched_users) == 0:
                raise ParameterError("No fuzzy matched user found for " + user)
            if len(matched_users) > 1:
                raise ParameterError("More than 1 user fuzzy match for " + user)
            user = matched_users[0]

        return agent[user].get_user()

    def get_gists(self, **args):
        host = args[self.HOST]
        hosts = self.hosts if host is None else [host]
        for host in hosts:
            agent = self.get_agent(host)
            user = args[self.USER]
            users = [user] if user else self.get_users(host)
            for user in users:
                if args[self.VERBOSE]:
                    print("user", user) # TODO: change to callback
                agent_user = self._get_user(agent, user, self._exact)
                for g in agent_user.get_gists():
                    gist = Gist(g, host)
                    if self._filter_gist(gist, **args):
                        yield gist

    def _filter_gist(self, gist, **args):
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
        tags = args[self.MATCH_TAGS]
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

    def download_gists(self, **args):
        for gist in self.get_gists(**args):
            local_parent = self._get_local_parent(gist)
            local_dir = join(local_parent, gist.id)
            if isdir(local_dir):
                self._pull_gists(local_dir, **args)
            else:
                self._clone_gists(gist, local_parent, **args)

    def _clone_gists(self, gist, local_parent, **args):
        if args[self.SSH]:
            gist_url = "git@" + gist.pull_url.replace('/', ':')[8:]
        else:
            gist_url = gist.pull_url
        cmd = "cd {dir}; git clone {verbose} {url}".format(
            dir=local_parent, verbose=("" if args[self.VERBOSE] else " -q"), url=gist_url)
        if args[self.DRY_RUN]:
            print(cmd)
        else:
            os.system(cmd)

    def _pull_gists(self, local_dir, **args):
        cmd = "cd {}; git pull{}".format(local_dir, "" if args[self.VERBOSE] else " -q")
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
        agent = self.get_agent(host)
        user = args[self.USER]
        if user is None:
            user = self._default_users[host] # at least 1
        agent_user = self._get_user(agent, user, self._exact)
        public = args[self.PUBLIC] or False
        desc = args[self.DESC] or self._default_description
        files = {}
        if paths:
            for path in paths:
                self._set_content(files, expanduser(path))
        else:
            self._set_content_from_stdin(files, **args)
        agent_user.create_gist(public, files, desc)

    def _set_content(self, files, path):
        with open(path, 'r') as f: # TODO: use binary mode depends on file type
            content = f.read()
            files[basename(path)] = InputFileContent(content)

    def _set_content_from_stdin(self, files, **args):
        filename = args[self.FILE_NAME] or self._default_filename
        content = sys.stdin.read()
        files[filename] = InputFileContent(content)

class ClientError(Exception):
    """Client-side error"""
    pass


class ConfigurationError(ClientError):
    """Configuration error"""
    pass


class ParameterError(ClientError):
    """Parameter error"""
    pass
