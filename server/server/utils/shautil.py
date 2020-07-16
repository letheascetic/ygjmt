# coding: utf-8

import hashlib


def calc_str_sha1(data):
    sha1obj = hashlib.sha1()
    sha1obj.update(str(data).encode('utf-8'))
    return sha1obj.hexdigest().upper()


def calc_str_sha256(data):
    sha256obj = hashlib.sha256()
    sha256obj.update(str(data).encode('utf-8'))
    return sha256obj.hexdigest().upper()


def calc_file_sha1(filepath):
    with open(filepath, 'rb') as f:
        sha1obj = hashlib.sha1()
        sha1obj.update(f.read())
    sha1 = sha1obj.hexdigest().upper()
    return sha1


def calc_file_sha256(filepath):
    with open(filepath, 'rb') as f:
        sha256obj = hashlib.sha256()
        sha256obj.update(f.read())
    sha256 = sha256obj.hexdigest().upper()
    return sha256
