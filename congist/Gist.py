# -*- coding: utf-8 -*-

"""
Gist represents a generic gist.
"""

class Gist:
    # assume gist is github.Gist.Gist object(temporarily)
    def __init__(self, gist):
        self._gist = gist

    def __repr__(self):
        return 'user={user}; url={url}; description={description}; public={public}'.format(
            user=self.user, url=self.api_url, description=self.description,
            public=self.public)

    def __str__(self):
        public = 'public' if self.public else 'secret'
        return '{url} {description} ({public})'.format(
            url=self.api_url, description=self.description, public=public)

    def get_info(self):
        return {
            "id": self.id,
            "description": self.description,
            "public": self.public,
            "starred": self.starred,
            "created": self.created,
            "updated": self.updated,
            "url": self.api_url,
            "files": { k : v.raw_url for k, v in self.files.items() }
        }

    @property
    def user(self):
        return self._gist.owner.login

    @property
    def id(self):
        return self._gist.id
 
    @property
    def description(self):
        return self._gist.description
    
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
    def files(self):
        return self._gist.files
    
    @property
    def created(self):
        return self._gist.created_at.isoformat()
    
    @property
    def updated(self):
        return self._gist.updated_at.isoformat()

    @property
    def files(self):
        return self._gist.files

    @property
    def starred(self):
        return self._gist.is_starred()