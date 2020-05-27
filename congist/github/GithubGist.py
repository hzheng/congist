# -*- coding: utf-8 -*-

"""
Gist represents a Github gist.
"""

from datetime import datetime

from congist.Gist import Gist
from congist.GistFile import GistFile


class GithubGist(Gist):
    TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self, session, gist, file_entries):
        assert isinstance(gist, dict), gist
        self._gist = gist
        self._session = session
        self._created_at = self._isoformat(gist['created_at'])
        self._updated_at = self._isoformat(gist['updated_at'])
        self._file_entries = [GistFile(self, f) for f in file_entries]

        super().__init__(session.username)

    def _isoformat(self, time_str):
        return datetime.strptime(time_str, self.TIME_FORMAT).isoformat()

    @property
    def id(self):
        return self._gist['id']

    @property
    def description(self):
        return self._gist['description'] or ""

    @property
    def public(self):
        return self._gist['public']

    @property
    def api_url(self):
        return self._gist['url']

    @property
    def html_url(self):
        return self._gist['html_url']

    @property
    def pull_url(self):
        return self._gist['git_pull_url']

    @property
    def push_url(self):
        return self._gist['git_push_url']

    @property
    def file_entries(self):
        return self._file_entries

    @property
    def created(self):
        return self._created_at

    @property
    def updated(self):
        return self._updated_at

    @property
    def starred(self):
        return self._session.is_starred(self)

    def set_starred(self, starred):
        self._session.set_starred(self, starred)

    def delete(self):
        self._session.delete(self)

    def set_description(self, description):
        self._session.update(self, description=description)

    def get_content(self, gist_file):
        assert isinstance(gist_file, GistFile), gist_file
        return self._session.get_content(gist_file)

    def update_file(self, gist_file, name, content=None):
        assert isinstance(gist_file, GistFile), gist_file
        attr = {}
        if name:
            attr['filename'] = name
        if content:
            attr['content'] = content
        return self._session.update(self, files={gist_file.name: attr})

    def delete_file(self, gist_file):
        assert isinstance(gist_file, GistFile), gist_file
        return self._session.update(self, files={gist_file.name: None})
