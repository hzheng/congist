# -*- coding: utf-8 -*-

"""
GithubAgent represents a Github agent.
"""

from congist.github.GithubSession import GithubSession


class GithubAgent:
    BASE_URL = "https://api.github.com"

    def __init__(self, gist_user):
        self._session = GithubSession(gist_user, self.BASE_URL)

    @property
    def host(self):
        type_name = type(self).__name__
        return type_name[:-5].lower()

    @property
    def username(self):
        return self._session.username

    def get_gists(self):
        yield from self._session.get_gists()

    def create_gist(self, desc, files, public):
        return self._session.create_gist(desc, files, public)
