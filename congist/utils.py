# -*- coding: utf-8 -*-

"""
Utility functions
"""

import importlib
import os
import re
import unicodedata
from os.path import basename, split, join, expanduser
from sys import stdin
from datetime import datetime, timezone, timedelta
from pathlib import Path
import dateutil.parser
from dateutil.relativedelta import relativedelta


class String:
    @staticmethod
    def equals(str1, str2, case_sensitive=False):
        if case_sensitive:
            return str1 == str2

        if str1 is None and str2 is None:
            return True
        if str1 is None or str2 is None:
            return False
        return String.casefold(str1) == String.casefold(str2)

    @staticmethod
    def contains(str1, str2, case_sensitive=False):
        if str2 is None:
            return True
        if str1 is None:
            return False
        if not case_sensitive:
            str1 = String.casefold(str1)
            str2 = String.casefold(str2)
        return str2 in str1

    @staticmethod
    def casefold(text):
        return unicodedata.normalize("NFKD", text.casefold()) if text else text

    @staticmethod
    def match(text, keyword, case_sensitive=False):
        if not isinstance(text, str):
            return False
        if not keyword:
            return True

        # return String.contains(text, keyword, case_sensitive)
        flag = 0 if case_sensitive else re.IGNORECASE
        return re.search(keyword, text, flag | re.DOTALL | re.MULTILINE)


class Collection:
    @staticmethod
    def contains(collection, word, case_sensitive=False):
        if word is None:
            return True
        if collection is None:
            return False

        if case_sensitive:
            return word in collection

        word = String.casefold(word)
        return any(word == String.casefold(e) for e in collection)


class File:
    TEXT_PAT_STR = 'text-pattern'

    @staticmethod
    def init(config):
        text_pattern = config[File.TEXT_PAT_STR]
        File.TEXT_PATTERN = re.compile(text_pattern)

    @staticmethod
    def mkdir(path, exist_ok=True, parents=True, mode=0o755):
        try:
            Path(path).mkdir(parents=parents, exist_ok=exist_ok, mode=mode)
        except (TypeError, AttributeError):
            os.makedirs(path, exist_ok=exist_ok, mode=mode)

    @staticmethod
    def is_binary(filename, content_type):
        if content_type.startswith('text'):
            return False
        return not File.TEXT_PATTERN.match(filename)

    @staticmethod
    def read(path, is_binary=False):
        if path:
            with open(expanduser(path), 'rb' if is_binary else 'r') as f:
                return f.read()
        else:
            if is_binary:
                return stdin.buffer.read()
            return stdin.read()

    @staticmethod
    def file_map(paths, filename, is_binary=False):
        files = {}
        key = 'content'
        if paths:
            for path in paths:
                files[basename(path)] = {key: File.read(path, is_binary)}
        else:
            files[filename] = {key: File.read(None, is_binary)}
        return files

    @staticmethod
    def config_path(path):
        if os.name != 'posix':
            dir_name, file_name = split(path)
            if file_name.startswith('.'):
                file_name = '_' + file_name[1:]
            path = join(dir_name, file_name)
        return expanduser(path)


class Time:
    FORMAT_PATTERN = re.compile(r'^(\d+)(y|M|d|h|m|s)?([+-])?$')
    UNIT_MAP = {
        'y': 'years',
        'M': 'months',
        'd': 'days',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds'
    }

    @staticmethod
    def check(time, expressions):
        """check if the given time satisfies all experssion."""
        target_time = dateutil.parser.isoparse(time)
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        for expr in expressions:
            if not Time._check(target_time, current_time, expr):
                return False
        return True

    @staticmethod
    def _check(target_time, current_time, expression):
        matched = Time.FORMAT_PATTERN.match(expression)
        if not matched:
            return False

        num, unit, relative = matched.groups()
        time_key = Time.UNIT_MAP[unit or 'd']
        src_time = current_time - relativedelta(**{time_key: int(num)})
        if relative == '+':
            return src_time > target_time
        if relative == '-':
            return src_time < target_time

        diff = abs(src_time - target_time)
        return diff < timedelta(**{time_key: 1})


class Type:

    @staticmethod
    def get_type(type_name):
        dot_pos = type_name.rindex('.')
        module_str = type_name[:dot_pos]
        type_str = type_name[dot_pos + 1:]
        module = importlib.import_module(module_str)
        return getattr(module, type_str)
