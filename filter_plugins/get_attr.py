#!/usr/bin/env python
"""
Ansible filter plugin to convert key/val based array
into a key:val dictionary.
Filter supports custom names for key/val.

Author: DevOps <devops@flaconi.de>
Version: v0.1
Date: 2018-05-24

Usage:
var: "{{ an.array | default({}) | get_attr('key', 'val') }}"
"""

class FilterModule(object):
    def filters(self):
        return {
            'get_attr': filter_list
        }
def filter_list(array, key, value):
    a = {}
    for i in array:
        a[i[key]] = i[value]
    return a
