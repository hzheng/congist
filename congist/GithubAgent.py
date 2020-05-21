# -*- coding: utf-8 -*-

"""
Github agent.
"""
import json

from github import Github, InputFileContent

from congist.GithubGist import GithubGist

class GithubAgent:

    def __init__(self, gist_user, index_file):
        github = Github(gist_user.access_token)
        self._gist_user = gist_user
        self._user = github.get_user()
        self._index_file = index_file
    
    @property
    def username(self):
        return self._gist_user.username

    def get_gists(self):
        for gist in self._user.get_gists():
            yield GithubGist(gist, self.username)

    def create_gist(self, contents, public, desc):
        files = { filename : InputFileContent(content)
                  for (filename, content) in contents.items()}
        gist = self._user.create_gist(public, files, desc)
        return GithubGist(gist, self.username)
    
    def get_local_gists(self, user):
        with open(self._index_file, 'r') as f:
            obj = json.load(f)[user]
            return obj