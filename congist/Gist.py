# -*- coding: utf-8 -*-

import re
from collections import namedtuple


"""
GistUser represents a gist user.
"""

GistUser = namedtuple('GistUser', ['username', 'access_token'])


"""
Gist represents a generic gist class.
"""

class Gist:
    TAGS = 'tags'
    TAG_MARK = '#'
    TITLE = 'title'
    SUBTITLE = 'subtitle'
    DESC_SPLIT = 'desc_split'
    DESC_JOIN = 'desc_join'

    @staticmethod
    def init(config):
        Gist._desc_pattern = re.compile(config[Gist.DESC_SPLIT])
        Gist._desc_format = config[Gist.DESC_JOIN]

    def __init__(self, username):
        self._username = username

        desc_dict = self._split_desc(self.description)
        self._title = desc_dict[self.TITLE]
        self._subtitle = desc_dict[self.SUBTITLE]
        self._tags = desc_dict[self.TAGS]

    def __repr__(self):
        return 'username={username}; url={url}; description={description}; public={public}'.format(
            username=self.username, url=self.api_url, description=self.description,
            public=self.public)

    def __str__(self):
        public = 'public' if self.public else 'secret'
        return '{url} {description} ({public})'.format(
            url=self.api_url, description=self.description, public=public)

    def get_info(self):
        return { # TODO: simplify
            'id': self.id,
            'description': self.description,
            'public': self.public,
            'starred': self.starred,
            'created': self.created,
            'updated': self.updated,
            'url': self.api_url,
            'files': self.files
        }

    @property
    def host(self):
        type_name = type(self).__name__
        return type_name[:-4].lower()

    @property
    def username(self):
        return self._username

    @property
    def id(self): ...
 
    @property
    def description(self): ...
 
    @property
    def tags(self):
        return self._tags
 
    @property
    def title(self):
        return self._title or self._subtitle or ''
    
    @property
    def public(self): ...
 
    @property
    def api_url(self): ...
 
    @property
    def html_url(self): ...
 
    @property
    def pull_url(self): ...
 
    @property
    def push_url(self): ...
 
    @property
    def html_url(self): ...
 
    @property
    def files(self):
        return {f.name: f.url for f in self.file_entries }
 
    @property
    def file_entries(self): ...
    
    @property
    def created(self): ...
    
    @property
    def updated(self): ...

    @property
    def starred(self): ...

    def set_starred(self, starred): ...

    def toggle_starred(self):
        self.set_starred(not self.starred)

    def delete(self): ...
    
    def set_description(self, description): ...
 
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