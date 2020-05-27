# -*- coding: utf-8 -*-

"""
LocalGist represents a local gist which is assumably synced with remote repository.
"""

import string
import unicodedata

from os.path import join

from congist.utils import File

from congist.Gist import Gist
from congist.GistFile import GistFile

class LocalGist(Gist):
    def __init__(self, values, username, local_base):
        for attr in self.ATTRS:
            setattr(self, "_" + attr, values[attr])
        self._local_base = local_base
        super().__init__(username)

    @property
    def id(self):
        return self._id
 
    @property
    def local_base(self):
        return self._local_base
 
    @property
    def description(self):
        return self._description or ""
 
    @property
    def public(self):
        return self._public
 
    @property
    def api_url(self):
        return self._api_url
 
    @property
    def file_entries(self):
        for name, file_entry in self._files.items():
            path = join(self.local_base, self.dir_name(self), name)
            yield GistFile(self, file_entry, path=path) 

    @property
    def created(self):
        return self._created
    
    @property
    def updated(self):
        return self._updated

    @property
    def starred(self):
        return self._starred
 
    def get_content(self, gist_file):
        assert isinstance(gist_file, GistFile), gist_file
        return File.read(gist_file.path, gist_file.binary)

    @staticmethod
    def dir_name(gist):
        name = LocalGist._clean_name(gist.title).replace(' ', '_')
        return name + "_" + gist.id[:6]

    VALID_FILENAME_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)

    @staticmethod
    def _clean_name(name):
        cleaned = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore')
        return ''.join(chr(c) for c in cleaned if chr(c) in LocalGist.VALID_FILENAME_CHARS)
