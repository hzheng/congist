# -*- coding: utf-8 -*-

"""
Gist represents a generic gist.
"""

class Gist:
    # assume gist is github.Gist.Gist object(temporarily)
    def __init__(self, gist, host):
        self._gist = gist
        self._host = host

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
            "files": { name : file.raw_url for name, file in self.files.items() }
        }

    @property
    def host(self):
        return self._host

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
    def starred(self):
        return self._gist.is_starred()

    def set_starred(self, starred):
        if starred:
            self._gist.set_starred()
        else:
            self._gist.reset_starred()

    def toggle_starred(self):
        self.set_starred(not self.starred)

    def delete(self):
        self._gist.delete()