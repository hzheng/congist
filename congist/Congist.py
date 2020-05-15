# -*- coding: utf-8 -*-

"""
Congist is the core worker.
"""

import os

from github import Github

from congist.Gist import Gist

class Congist:
    def __init__(self, config):
        self._githubs = {}
        local_base = config['local_base']
        if local_base[0] == '$':
            local_base = os.getenv(local_base[1:], os.getcwd())
        self._local_base = local_base
        self._local_dirs = {}
        repos = config['repos']
        self._hosts = repos.keys()
        for host, settings in repos.items():
            if host == 'github':
                for user in settings['users']:
                    username = user['username']
                    user_local_base = self.get_local_host_base(host) + "/" + username
                    os.makedirs(user_local_base, exist_ok=True)
                    self._local_dirs[host + "/" + username] = user_local_base
                    self._githubs[username] = Github(user['access_token'])
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

    def download_gist(self, gist, ssh, dry_run=False):
        local_parent = self._get_local_parent(gist)
        local_dir = local_parent + "/" + gist.id

        if os.path.isdir(local_dir):
            self._pull_gist(local_dir, dry_run)
        else:
            self._clone_gist(local_parent, gist, ssh, dry_run)

    def _clone_gist(self, local_parent, gist, ssh, dry_run):
        if ssh:
            gist_url = "git@" + gist.pull_url.replace('/', ':')[8:]
        else:
            gist_url = gist.pull_url
        cmd = "cd {}; git clone {}".format(local_parent, gist_url)
        if dry_run:
            print(cmd)
        else:
            os.system(cmd)

    def _pull_gist(self, local_dir, dry_run):
        cmd = "cd {}; git pull".format(local_dir)
        if dry_run:
            print(cmd)
        else:
            os.system(cmd)

    def _get_local_parent(self, gist):
        return self.get_local_dir("github/" + gist.user)

    def upload_gist(self, hosts=None, user=None, dry_run=False):
        if hosts is None:
            hosts = self.hosts
        for host in hosts:
            self._upload_gist(host, user, dry_run)

    def _upload_gist(self, host, user, dry_run):
        local_dir = self.get_local_host_base(host)
        if user:
            local_dir += "/" + user
        
        if not os.path.isdir(local_dir):
            return

        comment = 'commit via congist' #TODO customize commit message
        for subdir in os.listdir(local_dir):
            subdir = local_dir + "/" + subdir
            if not os.path.isdir(subdir):
                continue
            cmd = 'cd {} && git add -A && git commit -m "{}" && git push'.format(
                subdir, comment)
            if dry_run:
                print(cmd)
            else:
                os.system(cmd)