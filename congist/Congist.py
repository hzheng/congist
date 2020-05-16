# -*- coding: utf-8 -*-

"""
Congist is the core worker.
"""

import os

from github import Github

from congist.Gist import Gist

class Congist:
    LOCAL_BASE = 'local_base'
    REPOS = 'repos'
    USERNAME = 'username'
    USERS = 'users'
    ACCESS_TOKEN = 'access_token'
    GITHUB = 'github'

    def __init__(self, config):
        self._githubs = {}
        local_base = config[self.LOCAL_BASE]
        if local_base[0] == '$':
            local_base = os.getenv(local_base[1:], os.getcwd())
        self._local_base = local_base
        self._local_dirs = {}
        repos = config[self.REPOS]
        self._hosts = repos.keys()
        for host, settings in repos.items():
            if host == self.GITHUB:
                for user in settings[self.USERS]:
                    username = user[self.USERNAME]
                    user_local_base = self.get_local_host_base(host) + "/" + username
                    os.makedirs(user_local_base, exist_ok=True)
                    self._local_dirs[host + "/" + username] = user_local_base
                    self._githubs[username] = Github(user[self.ACCESS_TOKEN])
            else: # currently only support GitHub
                pass

    @property
    def hosts(self):
        return self._hosts

    @property
    def local_base(self):
        return self._local_base

    def get_local_host_base(self, host):
        return self.local_base + "/" + host

    def get_local_dir(self, user):
        return self._local_dirs[user]

    @property
    def users(self):
        return self._githubs.keys()

    def get_gists(self, user):
        github_user = self._githubs[user].get_user()
        return [Gist(gist) for gist in github_user.get_gists()]

    def get_user_index(self, user):
        return [gist.get_info() for gist in self.get_gists(user)]

    def get_index(self):
        return { u: self.get_user_index(u) for u in self.users}

    def download_gist(self, gist, **args):
        local_parent = self._get_local_parent(gist)
        local_dir = local_parent + "/" + gist.id

        if os.path.isdir(local_dir):
            self._pull_gist(local_dir, **args)
        else:
            self._clone_gist(local_parent, gist, **args)

    def _clone_gist(self, local_parent, gist, **args):
        if args['ssh']:
            gist_url = "git@" + gist.pull_url.replace('/', ':')[8:]
        else:
            gist_url = gist.pull_url
        cmd = "cd {dir}; git clone {verbose} {url}".format(
            dir=local_parent, verbose=("" if args['verbose'] else " -q"), url=gist_url)
        if args['dry_run']:
            print(cmd)
        else:
            os.system(cmd)

    def _pull_gist(self, local_dir, **args):
        cmd = "cd {}; git pull{}".format(local_dir, "" if args['verbose'] else " -q")
        if args['dry_run']:
            print(cmd)
        else:
            os.system(cmd)

    def _get_local_parent(self, gist):
        return self.get_local_dir(self.GITHUB + "/" + gist.user)

    def upload_gist(self, user_, **args):
        host = args['host']
        hosts = self.hosts if host is None else [host]
        for host in hosts:
            self._upload_gist(host, user_, **args)

    GIT_COMMENT = 'commit via congist' #TODO customizable
    GIT_PUSH = 'git add -A && (git diff --cached --exit-code >/dev/null || (git commit -m "{comment}" {verbose} && git push {verbose}))'

    def _upload_gist(self, host_, user_, **args):
        local_dir = self.get_local_host_base(host_)
        if user_:
            local_dir += "/" + user_
        if not os.path.isdir(local_dir):
            return

        for subdir in os.listdir(local_dir):
            subdir = local_dir + "/" + subdir
            if not os.path.isdir(subdir):
                continue
            cmd = ('cd {subdir} &&' + self.GIT_PUSH).format(
                subdir=subdir, comment=self.GIT_COMMENT,
                verbose=("" if args['verbose'] else "-q"))
            if args['dry_run']:
                print(cmd)
            else:
                os.system(cmd)
