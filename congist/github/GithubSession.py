# -*- coding: utf-8 -*-

"""
Github session.
Reference: http://developer.github.com/v3/gists
"""

import json
import requests

from congist.github.GithubGist import GithubGist
from congist.GistFile import GistFile


class GithubSession:
    def __init__(self, gist_user, base_url):
        username = self._username = gist_user.username
        self._session = requests.Session()
        self._session.auth = (username, gist_user.access_token)
        self.BASE_URL = base_url
        # self.GIST_URL = base_url + '/users/' + username + '/gists'
        self.GIST_URL = base_url + '/gists'
        self.STAR_URL = "{}/star"

    @property
    def username(self):
        return self._username

    def get_gists(self):
        for gist in self._session.get(self.GIST_URL).json():
            file_entries = [self._gist_attrs(f)
                            for f in gist['files'].values()]
            yield GithubGist(self, gist, file_entries)

    def _gist_attrs(self, f):
        return {
            'name': f['filename'],
            'url': f['raw_url'],
            'size': f['size'],
            'type': f['type'],
        }

    def create_gist(self, desc, files, public):
        data = self._form_data(desc, files, public)
        resp = self._session.post(self.GIST_URL, data=data)
        return resp.status_code == 201

    def get_content(self, gist_file):
        assert isinstance(gist_file, GistFile), gist_file

        resp = self._session.get(gist_file.url)
        # TODO: check if size are correct
        return resp.content if gist_file.binary else resp.text

    def is_starred(self, gist):
        resp = self._session.get(self.STAR_URL.format(gist.api_url))
        return resp.status_code == 204

    def set_starred(self, gist, starred):
        url = self.STAR_URL.format(gist.api_url)
        if starred:
            resp = self._session.put(url)
        else:
            resp = self._session.delete(url)
        return resp.status_code == 204

    def delete(self, gist):
        resp = self._session.delete(gist.api_url)
        return resp.status_code == 204

    def update(self, gist, description=None, files=None):
        data = self._form_data(description, files)
        resp = self._session.patch(gist.api_url, data=data)
        return resp.status_code == 200

    def _form_data(self, description, files, public=None):
        params = {}
        if description:
            params['description'] = description
        if files:
            params['files'] = files
        if public is not None:
            params['public'] = public
        return json.dumps(params)
