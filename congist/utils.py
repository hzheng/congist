# -*- coding: utf-8 -*-

"""
Utility functions
"""

import re
import unicodedata
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

from os.path import basename, expanduser
from sys import stdin

class String:
    @staticmethod
    def equals(str1, str2, case_sensitive=False):
        if case_sensitive:
            return str1 == str2

        if str1 is None and str2 is None: return True
        if str1 is None or str2 is None: return False
        return String.casefold(str1) == String.casefold(str2)

    @staticmethod
    def contains(str1, str2, case_sensitive=False):
        if str2 is None: return True
        if str1 is None: return False
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

class Array:
    @staticmethod
    def contains(arr, s, case_sensitive=False):
        if s is None:
            return True
        if arr is None:
            return False

        if not case_sensitive:
            str1 = String.casefold(str1)
            str2 = String.casefold(str2)
        return str2 in str1 

class File:
    TEXT_PATTERN = 'text-pattern'

    @staticmethod
    def init(config):
        text_pattern = config[File.TEXT_PATTERN]
        File.TEXT_PATTERN = re.compile(text_pattern)

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

class Time:
    FORMAT_PATTERN = re.compile('^(\d+)(y|M|d|h|m|s)?([+-])?$')
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
        current_time = datetime.now()
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
        return diff < timedelta(**{time_key : 1})
