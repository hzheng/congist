# -*- coding: utf-8 -*-

"""
GistFile represents a gist file.
"""

import json

from congist.Gist import Gist
from congist.utils import File

class GistFile:

    def __init__(self, gist, file_entry, path=None):
        assert isinstance(gist, Gist), gist
        assert isinstance(file_entry, dict), file_entry

        self._gist = gist
        self._path = path
        self._name = file_entry['name']
        self._url = file_entry['url']
        self._size = file_entry['size']
        self._content_type = file_entry['type']
        self._binary = File.is_binary(self._name, self._content_type)
        self._content = None

    def __repr__(self):
        return json.dumps(self.attrs)
    
    @property
    def attrs(self):
        return {'name': self.name, 'url': self.url, 'type': self.content_type,
                'size': self.size}
    
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
        self._load_content()
        return self._content
    
    @property
    def size(self):
        return self._size
    
    @property
    def content_type(self):
        return self._content_type
    
    @property
    def binary(self):
        return self._binary

    def _load_content(self):
        if self._content is None:
            self._content = self._gist.get_content(self)
        return self._content

    def delete(self):
        return self._gist.delete_file(self)

    def update(self, name, content):
        return self._gist.update_file(self, name, content)
