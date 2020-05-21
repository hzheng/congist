# -*- coding: utf-8 -*-

"""
Github agent.
"""

from github import Github, InputFileContent

class GithubAgent:

    def __init__(self, access_token):
        github = Github(access_token)
        self._user = github.get_user()
    
    def get_gists(self):
        return self._user.get_gists()

    def create_gist(self, contents, public, desc):
        files = { filename : InputFileContent(content)
                  for (filename, content) in contents.items()}
        self._user.create_gist(public, files, desc)