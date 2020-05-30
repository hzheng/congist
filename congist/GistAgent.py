# -*- coding: utf-8 -*-

"""
GistAgent represents a generic gist agent.
"""


class GistAgent():

    @property
    def host(self): ...

    @property
    def username(self): ...

    def get_gists(self): ...

    def create_gist(self, files, desc="", public=False): ...
