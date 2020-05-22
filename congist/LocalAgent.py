# -*- coding: utf-8 -*-

"""
Local agent.
"""

import json

from congist.LocalGist import LocalGist

class LocalAgent:

    def __init__(self, remote_agent, local_base, index_file):
        self._remote = remote_agent
        self._local_base = local_base
        self._index_file = index_file
 
    @property
    def host(self):
        return self._remote.host
 
    @property
    def username(self):
        return self._remote.username
 
    @property
    def local_base(self):
        return self._local_base
 
    @property
    def index_file(self):
        return self._index_file
    
    def get_gists(self):
        with open(self.index_file, 'r') as f:
            user = self.username
            for obj in json.load(f)[user]:
                yield LocalGist(obj, user, self.local_base)