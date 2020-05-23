# -*- coding: utf-8 -*-

"""
Utility functions
"""

import unicodedata

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

class Array:
    @staticmethod
    def contains(arr, s, case_sensitive=False):
        if s is None: return True
        if arr is None: return False

        if not case_sensitive:
            str1 = String.casefold(str1)
            str2 = String.casefold(str2)
        return str2 in str1 

class File:
    @staticmethod
    def get_content(path):
        try:
            with open(path, "r") as f:
                return f.read(), False
        except UnicodeDecodeError as e:
            with open(path, "rb") as f:
                return f.read(), True
