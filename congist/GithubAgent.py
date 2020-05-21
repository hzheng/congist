# -*- coding: utf-8 -*-

"""
Github agent.
"""
import json

from github import Github, InputFileContent

from congist.GithubGist import GithubGist

class GithubAgent:

    def __init__(self, access_token, index_file):
        github = Github(access_token)
        self._user = github.get_user()
        self._index_file = index_file
    
    def get_gists(self):
        for gist in self._user.get_gists():
            yield GithubGist(gist)

    def create_gist(self, contents, public, desc):
        files = { filename : InputFileContent(content)
                  for (filename, content) in contents.items()}
        gist = self._user.create_gist(public, files, desc)
        return GithubGist(gist)