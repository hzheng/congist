# -*- coding: utf-8 -*-

"""
GistFile represents a gist file.
"""

from congist.utils import File

class GistFile:

    def __init__(self, name, url, path=None, content=None):
        self._name = name
        self._content = content
        self._url = url
        self._path = path
        self._binary = False
    
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
        self._check_content()
        return self._content
    
    @property
    def binary(self):
        self._check_content()
        return self._binary

    def _check_content(self):
        if self._content is None and self._path:
            self._content, self._binary = File.read(self._path)