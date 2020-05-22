# -*- coding: utf-8 -*-

"""
GistFile represents a gist file.
"""

class GistFile:

    def __init__(self, name, url, path=None, content=None):
        self._name = name
        self._content = content
        self._url = url
        self._path = path
    
    @property
    def name(self):
        return self._name
    
    @property
    def url(self):
        return self._url
    
    @property
    def path(self):
        return self._path
    
    @property
    def content(self):
        if self._content is None and self._path:
            with open(self._path, 'rb') as f:
                self._content = f.read()
        return self._content