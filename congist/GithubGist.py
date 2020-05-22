# -*- coding: utf-8 -*-

"""
Gist represents a Github gist.
"""

from congist.Gist import Gist
from congist.GistFile import GistFile

class GithubGist(Gist):
    # assume gist is github.Gist.Gist object(temporarily)
    def __init__(self, gist, username):
        self._gist = gist
        super().__init__(username)

    @property
    def id(self):
        return self._gist.id
 
    @property
    def description(self):
        return self._gist.description or ""
    
    @property
    def public(self):
        return self._gist.public
 
    @property
    def api_url(self):
        return self._gist.url
 
    @property
    def html_url(self):
        return self._gist.html_url
 
    @property
    def pull_url(self):
        return self._gist.git_pull_url
 
    @property
    def push_url(self):
        return self._gist.git_push_url
 
    @property
    def html_url(self):
        return self._gist.html_url
 
    @property
    def file_entries(self):
        for name, f in self._gist.files.items():
            yield GistFile(name=name, content=f.content, url=f.raw_url) 
    
    @property
    def created(self):
        return self._gist.created_at.isoformat()
    
    @property
    def updated(self):
        return self._gist.updated_at.isoformat()

    @property
    def starred(self):
        return self._gist.is_starred()

    def set_starred(self, starred):
        if starred:
            self._gist.set_starred()
        else:
            self._gist.reset_starred()

    def delete(self):
        self._gist.delete()
    
    def set_description(self, description):
        self._gist.edit(description=description)
