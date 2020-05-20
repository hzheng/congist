# -*- coding: utf-8 -*-

import re

"""
Gist represents a generic gist.
"""

class Gist:
    TAGS = 'tags'
    TAG_MARK = '#'
    TITLE = 'title'
    DESC_SPLIT = 'desc_split'
    DESC_JOIN = 'desc_join'

    @staticmethod
    def init(config):
        Gist._desc_pattern = re.compile(config[Gist.DESC_SPLIT])
        Gist._desc_format = config[Gist.DESC_JOIN]

    # assume gist is github.Gist.Gist object(temporarily)
    def __init__(self, gist, host):
        self._gist = gist
        self._host = host
        self._tags = self._split_desc(self.description)[self.TAGS]

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
            'id': self.id,
            'description': self.description,
            'public': self.public,
            'starred': self.starred,
            'created': self.created,
            'updated': self.updated,
            'url': self.api_url,
            'files': { name : file.raw_url for name, file in self.files.items() }
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
        return self._gist.description or ""
 
    @property
    def tags(self):
        return self._tags
    
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
    
    def set_description(self, description):
        self._gist.edit(description=description)
 
    def set_tags(self, tags):
        desc = self._split_desc(self.description)
        desc[self.TAGS] = tags
        self.set_description(self._join_desc(desc))
 
    def has_tags(self, tags):
        return all(t in self.tags for t in tags)
 
    def _split_desc(self, desc):
        matched = self._desc_pattern.match(desc).groupdict()
        matched.update({k: v.strip() for k, v in matched.items() if isinstance(v, str)})
        tags = matched[self.TAGS]
        tags = tags.split(self.TAG_MARK) if tags else []
        matched[self.TAGS] = {t.strip() for t in tags if t.strip()}
        return matched

    def _join_desc(self, desc):
        format_desc = desc.copy()
        tags = (" " + self.TAG_MARK).join(desc[self.TAGS])
        if tags:
            tags = (" " + self.TAG_MARK) + tags
        format_desc[self.TAGS] = tags
        joined = self._desc_format.format(**format_desc)
        if not desc[self.TITLE]: # skip empty title
            joined = joined[joined.find(' ') + 1:]
        return joined