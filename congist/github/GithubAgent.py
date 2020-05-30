# -*- coding: utf-8 -*-

"""
GithubAgent represents a Github agent.
"""

from congist.GistAgent import GistAgent

from congist.github.GithubSession import GithubSession


class GithubAgent(GistAgent):
    BASE_URL = "https://api.github.com"

    def __init__(self, gist_user):
        self._session = GithubSession(gist_user, self.BASE_URL)
        self._gist_user = gist_user

    @property
    def host(self):
        type_name = type(self).__name__
        return type_name[:-5].lower()

    @property
    def username(self):
        return self._session.username

    @property
    def ssh(self):
        return self._gist_user.ssh

    @property
    def gist_user(self):
        return self._gist_user

    def get_gists(self):
        yield from self._session.get_gists()

    def create_gist(self, files, desc="", public=False):
        return self._session.create_gist(desc, files, public)
