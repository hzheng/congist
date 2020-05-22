# -*- coding: utf-8 -*-

"""
LocalGist represents a local gist which is assumably synced with remote repository.
"""

import string
import unicodedata

from os.path import join

from congist.Gist import Gist, GistFile

class LocalGist(Gist):
    def __init__(self, obj, username, local_base):
        self._id = obj['id']
        self._description = obj['description']
        self._url = obj['url']
        self._public = obj['public']
        self._starred = obj['starred']
        self._created = obj['created']
        self._updated = obj['updated']
        self._files = obj['files']
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
        return self._url
 
    @property
    def file_entries(self):
        for name, url in self._files.items():
            path = join(self.local_base, self.dir_name(self), name)
            with open(path, 'rb') as f:
                content = f.read()
                yield name, GistFile(name=name, content=content, url=url) 

    @property
    def created(self):
        return self._created
    
    @property
    def updated(self):
        return self._updated

    @property
    def starred(self):
        return self._starred

    @staticmethod
    def dir_name(gist):
        name = LocalGist._clean_name(gist.title).replace(' ', '_')
        return name + "_" + gist.id[:6]

    VALID_FILENAME_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)

    @staticmethod
    def _clean_name(name):
        cleaned = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore')
        return ''.join(chr(c) for c in cleaned if chr(c) in LocalGist.VALID_FILENAME_CHARS)
