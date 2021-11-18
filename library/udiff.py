#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, cytopia <cytopia@everythingcli.org>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '2.0',
                    'supported_by': 'community',
                    'status': ['preview']}

DOCUMENTATION = '''
---
module: udiff
author: cytopia (@cytopia)

short_description: udiff compare strings, files or command outputs in raw or file specific normalized version.
description:
    - udiff compare a string, file or command output against a string file or command output.
    - Check mode is only supported when diffing strings or files, commands will only be executed in actual run.
    - More examples at U(https://github.com/cytopia/ansible-module-diff)
version_added: "2.4"
options:
    source:
        description:
            - The source input to diff. Can be a string, contents of a file or output from a command, depending on I(source_type).
        required: true
        default: null
        aliases: []

    target:
        description:
            - The target input to diff. Can be a string, contents of a file or output from a command, depending on I(target_type).
        required: true
        default: null
        aliases: []

    source_type:
        description:
            - Specify the input type of I(source).
        required: false
        default: string
        choices: [string, file, command]
        aliases: []

    target_tyoe:
        description:
            - Specify the input type of I(target).
        required: false
        default: string
        choices: [string, file, command]
        aliases: []

    diff:
        description:
            - Specify the diff type.
            - Currently only raw and yaml are supported.
            - In case of yaml, both inputs are normalized, comments removed and their keys are sorted.
        required: false
        default: raw
        choices: [raw, yaml]
        aliases: []

    diff_yaml_ignore:
        description:
            - List of keys to ignore for yaml diff
        required: false
        default: []
        aliases: []
'''

EXAMPLES = '''
# Diff compare two strings
- udiff:
    source: "foo"
    target: "bar"
    source_type: string
    target_type: string

# Diff compare variable against template file (as strings)
- udiff:
    source: "{{ lookup('template', tpl.yml.j2) }}"
    target: "{{ my_var }}"
    source_type: string
    target_type: string

# Diff compare string against command output
- udiff:
    source: "/bin/bash"
    target: "which bash"
    source_type: string
    target_type: command

# Diff compare file against command output
- udiff:
    source: "/etc/hostname"
    target: "hostname"
    source_type: file
    target_type: command

# Diff compare two normalized yaml files (sorted keys and comments stripped),
# but additionally ignore the yaml keys: 'creationTimestamp' and 'metadata'
- udiff:
    source: /tmp/file-1.yml
    target: /tmp/file-2.yml
    source_type: file
    target_type: file
    diff: yaml
    diff_yaml_ignore:
      - creationTimestamp
      - metadata
'''

RETURN = '''
udiff:
    description: diff output
    returned: success
    type: string
    sample: + this line was added
'''

# -------------------------------------------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------------------------------------------
#pylint: disable=wrong-import-position

# Python default imports
import copy
import os
import re
import subprocess
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import ruamel.yaml

# Python Ansible imports
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


# -------------------------------------------------------------------------------------------------
# CLASSES
# -------------------------------------------------------------------------------------------------

class MyYaml(object):
    '''ruamel based Yaml class'''

    def __str2yml(self, string):
        '''Safely load yaml'''
        yaml = YAML()
        try:
            return yaml.load(string)
        except Exception as exc:
            # We might already have yaml
            return string

    def __fixyml(self, data):
        '''
        This function iterates through an already loaded yaml (dict)
        variable recursively and converts any inline yaml/json strings
        to correct python dicts.
        '''

        # It's a dict, so recurse
        if isinstance(data, dict):
            d = dict()
            for key, val in data.items():
                d[key] = self.__fixyml(val)
            return d
        # It's a list, so recurse
        elif isinstance(data, list):
            l = list()
            for key in data:
                l.append(self.__fixyml(key))
            return l
        # It's a string or inline dict/list/json
        else:
            k = self.__str2yml(data)
            if isinstance(k, dict):
                d = dict()
                for key, val in k.items():
                    d[key] = self.__fixyml(val)
                return d
            elif isinstance(k, list):
                l = list()
                for key in k:
                    l.append(self.__fixyml(key))
                return l
            elif k is None:
                k = ''

            return k

    def load(self, string):
        '''Load string into yaml (python dict)'''
        data = self.__str2yml(string)
        data = self.__fixyml(data)
        return data

    def dump(self, data):
        '''return yaml string from python dict'''
        yaml = YAML()
        yaml.indent(mapping=4, sequence=6, offset=3)
        stream = StringIO()
        ruamel.yaml.safe_dump(data, stream, default_flow_style=False)
        return stream.getvalue()

    def split(self, string):
        '''
        Split a string, which contains multiple yaml definitions separated by '---'
        into a list of strings containing single yaml strings per item.
        '''
        sections = list()

        for section in re.split("^---$", string, flags=re.MULTILINE):
            sections.append(section)

        return sections


# -------------------------------------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------------------------------------

def shell_exec(command):
    '''
    Execute raw shell command and return exit code and output
    '''
    cpt = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    stdout, stderr = cpt.communicate()

    # Get return code from process
    return_code = cpt.returncode

    # Return code and output
    return return_code, to_bytes(stdout).decode("utf-8")


def pop_recursive(dictionary, keys):
    '''
    Pop keys in a nested dictionary.
    '''
    # Return immediately on empty dicts or keys
    if not dictionary or not keys:
        return dictionary

    # make sure the_keys is a set to get O(1) lookups
    #if type(keys) is not set:
    #    keys = set(keys)
    if isinstance(dictionary, dict):
        for key, val in copy.copy(dictionary).items():
            if key in keys:
                del dictionary[key]
            if isinstance(val, dict):
                pop_recursive(val, keys)

    return dictionary


def normalize_yaml(string, ignore):
    '''
    Convert string to yaml, normalize and sort it and convert it back to string.
    Additionally if 'ignore' is specified, all keys matching the specified keys are removed
    in order for them to not appread in the diff output.
    This function also works with a single yaml file that has multiple --- separators.
    '''
    yml = MyYaml()
    sections = list()

    # Loop over yaml '---' separators
    for section in yml.split(string):
        try:
            # Load string into object
            data = yml.load(section)

            # We have a valid dictionary
            if isinstance(data, dict):
                data = pop_recursive(data, ignore)
            # Convert None object to empty string
            elif data is None:
                data = dict()

            # Append yaml sections to list
            sections.append(data)

        except Exception as exc:
            return (False, exc)


    # Sort the list by keys: metadata.name
    if 'metadata' in ignore:
      s_sections = sections
    else:
      s_sections = sorted(sections, key=lambda k: k['metadata']['name'])

    output = ''
    for section in s_sections:
        output = output + "---\n" + yml.dump(section) + "\n\n"

    return (True, output)


def normalize_input(input_data, input_data_name, module):
    '''
    Normalize input to specified diff_type.
    input_data: value of 'source' or 'target'
    input_data_name: 'source' or 'target'
    '''

    # Get chosen diff type
    diff_type = module.params.get('diff')

    # Normalize yaml
    if diff_type == 'yaml':
        ignore = module.params.get('diff_yaml_ignore')
        succ, input_data = normalize_yaml(input_data, ignore)
        if not succ:
            module.fail_json(msg="Convert to yaml failed on %s: %s" % (input_data_name, input_data))

    return input_data


def retrieve_input(direction, module):
    '''
    Retrieve and evaluate Ansible module input arguments.
    direction can either be 'source' or 'target'.
    Input arguments:
      * target
      * target_name
      * source
      * source_name
    '''
    input_data_name = direction
    input_type_name = direction + '_type'

    input_data = module.params.get(input_data_name)
    input_type = module.params.get(input_type_name)

    # Input is a file
    if input_type == 'file':
        with open(input_data, 'rt') as fpt:
            input_data = fpt.read().decode("UTF-8")
    # Input is a command
    elif input_type == 'command':
        if module.check_mode:
            result = dict(
                changed=False,
                msg="This module does not support check mode when " +
                input_type_name + " is 'command'.",
                skipped=True
            )
            module.exit_json(**result)
        else:
            command = input_data
            ret, input_data = shell_exec(command)
            if ret != 0:
                module.fail_json(msg="%s command failed: %s" % (input_data_name, input_data))

    # Return evaluated input
    return input_data


def diff_module_validation(module):
    '''
    Validate for correct module call/usage in ansible.
    '''
    source = module.params.get('source')
    target = module.params.get('target')
    source_type = module.params.get('source_type')
    target_type = module.params.get('target_type')

    # Validate source
    if source_type == 'file':
        b_source = to_bytes(source, errors='surrogate_or_strict')
        if not os.path.exists(b_source):
            module.fail_json(msg="source %s not found" % (source))
        if not os.access(b_source, os.R_OK):
            module.fail_json(msg="source %s not readable" % (source))
        if os.path.isdir(b_source):
            module.fail_json(msg="udiff does not support recursive diff of directory: %s" % (source))

    # Validate target
    if target_type == 'file':
        b_target = to_bytes(target, errors='surrogate_or_strict')
        if not os.path.exists(b_target):
            module.fail_json(msg="target %s not found" % (target))
        if not os.access(b_target, os.R_OK):
            module.fail_json(msg="target %s not readable" % (target))
        if os.path.isdir(b_target):
            module.fail_json(msg="udiff does not support recursive diff of directory: %s" % (target))

    return module


def init_ansible_module():
    '''
    Initialize Ansible Module.
    '''
    return AnsibleModule(
        argument_spec=dict(
            source=dict(type='str', required=True, default=None),
            target=dict(type='str', required=True, default=None),
            source_type=dict(
                type='str',
                required=False,
                default='string',
                choices=['string', 'file', 'command']
            ),
            target_type=dict(
                type='str',
                required=False,
                default='string',
                choices=['string', 'file', 'command']
            ),
            diff=dict(
                type='str',
                required=False,
                default='raw',
                choices=['raw', 'yaml']
            ),
            diff_yaml_ignore=dict(
                type='list',
                required=False,
                default=[],
            )
        ),
        supports_check_mode=True
    )


def main():
    '''
    Main entry point
    '''
    # Initialize module
    module = init_ansible_module()

    # Validate module
    module = diff_module_validation(module)

    # Retrieve converted module input
    source = retrieve_input('source', module)
    target = retrieve_input('target', module)

    # Normalize input
    source = normalize_input(source, 'source', module)
    target = normalize_input(target, 'target', module)

    # Ansible diff output
    diff = {
        'before': target,
        'after': source,
    }
    # Did we have any changes?
    changed = (source != target)

    # Ansible module returned variables
    result = dict(
        diff=diff,
        changed=changed
    )

    # Exit ansible module call
    module.exit_json(**result)


if __name__ == '__main__':
    main()
