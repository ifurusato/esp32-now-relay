#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2025-06-02
# modified: 2026-06-23
#
# This is a simple YAML parser for MicroPython, supporting a subset of the
# standard YAML grammar, as described below:
#
# - nested dictionaries with consistent indentation (4 spaces)
# - scalars: strings, integers, floats, booleans, and nulls
# - flat lists of scalar values
# - inline comments (after values, using '#')
# - automatic type conversion for scalars
# - pretty-printing in either JSON or YAML format
#
# Any features beyond those listed above, e.g., nested lists, multiline
# strings, anchors, complex keys, inline dictionaries and complex YAML
# syntax are not supported.

class FileNotFoundError(Exception):
    '''
    An exception thrown when encountering a reference to a file that does not exist.
    '''
    pass

def load(fpath, suppress_error_message=False):
    try:
        with open(fpath, 'r') as f:
            text = f.read()
            return parse(text)
    except OSError as e:
        if not suppress_error_message:
            print('{} raised opening file: {}'.format(type(e), e))
        raise FileNotFoundError("file not found: {}".format(fpath))

def dump(obj, indent=4):
    import pprint
    # delegate the call to pprint.pretty_print
    pprint.pretty_print(obj, indent=indent)

def parse(text):
    lines = text.split('\n')
    def parse_value(val):
        v = val.strip()
        if v == '' or v.lower() in ('null', 'none'):
            return None
        if v.lower() == 'true':
            return True
        if v.lower() == 'false':
            return False
        try:
            if '.' in v:
                return float(v)
            if v.lower().startswith('0x'):
                return int(v, 16)
            return int(v)
        except ValueError:
            return v.strip('\'"')
    root = {}
    # stack stores tuples of (indent_level, container_object, is_list_item)
    stack = [(-1, root, False)]
    for i, line in enumerate(lines):
        line = line.split('#', 1)[0]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(' '))
        content = line.strip()
        # pop stack until we find the correct parent indentation level
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent_indent, parent, is_item = stack[-1]
        if content.startswith('- '):
            if not isinstance(parent, list):
                raise ValueError('list item found but parent is not a list')
            list_content = content[2:].strip()
            if ':' in list_content:
                # case: Mixed list item and mapping (- id: 0)
                item_dict = {}
                parent.append(item_dict)
                
                # Check for quoted keys in mixed list mappings
                if list_content.startswith(('"', "'")):
                    quote_char = list_content[0]
                    end_quote_idx = list_content.find(quote_char, 1)
                    split_idx = list_content.find(':', end_quote_idx)
                    if split_idx == -1:
                        raise ValueError('invalid line (no colon): {}'.format(content))
                    key = list_content[:split_idx].strip(' \'"')
                    val = list_content[split_idx + 1:].strip()
                else:
                    key, val = list_content.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                
                val_obj = parse_value(val) if val != '' else {}
                item_dict[key] = val_obj
                # push the item dictionary context.
                stack.append((indent, item_dict, True))
                if val == '' and isinstance(val_obj, (dict, list)):
                    stack.append((indent + 2, val_obj, False))
            else:
                # case: Primitive scalar value sequence (- value)
                parent.append(parse_value(list_content))
        else:
            # Check for a quoted key to avoid splitting inside the quotes
            if content.startswith(('"', "'")):
                quote_char = content[0]
                end_quote_idx = content.find(quote_char, 1)
                split_idx = content.find(':', end_quote_idx)
                if split_idx == -1:
                    raise ValueError('invalid line (no colon): {}'.format(content))
                key = content[:split_idx].strip(' \'"')
                val = content[split_idx + 1:].strip()
            else:
                if ':' not in content:
                    raise ValueError('invalid line (no colon): {}'.format(content))
                key, val = content.split(':', 1)
                key = key.strip()
                val = val.strip()
                
            if val == '':
                # lookahead to determine container type
                val_obj = {}
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].split('#', 1)[0].rstrip()
                    if not next_line.strip():
                        continue
                    if next_line.lstrip().startswith('- '):
                        val_obj = []
                    break
            else:
                val_obj = parse_value(val)
            # if our immediate parent on the stack is an active list item dictionary,
            # we insert keys directly into it rather than failing.
            if isinstance(parent, dict):
                parent[key] = val_obj
            else:
                raise ValueError('expected dict as parent')

            if val == '' and isinstance(val_obj, (dict, list)):
                stack.append((indent, val_obj, False))
    return root

def x_parse(text):
    lines = text.split('\n')
    def parse_value(val):
        v = val.strip()
        if v == '' or v.lower() in ('null', 'none'):
            return None
        if v.lower() == 'true':
            return True
        if v.lower() == 'false':
            return False
        try:
            if '.' in v:
                return float(v)
            if v.lower().startswith('0x'):
                return int(v, 16)
            return int(v)
        except ValueError:
            return v.strip('\'"')
    root = {}
    # stack stores tuples of (indent_level, container_object, is_list_item)
    stack = [(-1, root, False)]
    for i, line in enumerate(lines):
        line = line.split('#', 1)[0]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(' '))
        content = line.strip()
        # pop stack until we find the correct parent indentation level
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent_indent, parent, is_item = stack[-1]
        if content.startswith('- '):
            if not isinstance(parent, list):
                raise ValueError('list item found but parent is not a list')
            list_content = content[2:].strip()
            if ':' in list_content:
                # case: Mixed list item and mapping (- id: 0)
                item_dict = {}
                parent.append(item_dict)
                key, val = list_content.split(':', 1)
                key = key.strip()
                val = val.strip()
                val_obj = parse_value(val) if val != '' else {}
                item_dict[key] = val_obj
                # push the item dictionary context.
                # sub-keys at the same visual depth (+2 spaces from dash or aligned)
                # will match this structural level.
                stack.append((indent, item_dict, True))
                if val == '' and isinstance(val_obj, (dict, list)):
                    stack.append((indent + 2, val_obj, False))
            else:
                # case: Primitive scalar value sequence (- value)
                parent.append(parse_value(list_content))
        else:
            if ':' not in content:
                raise ValueError('invalid line (no colon): {}'.format(content))
            key, val = content.split(':', 1)
            key = key.strip()
            val = val.strip()
            if val == '':
                # lookahead to determine container type
                val_obj = {}
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].split('#', 1)[0].rstrip()
                    if not next_line.strip():
                        continue
                    if next_line.lstrip().startswith('- '):
                        val_obj = []
                    break
            else:
                val_obj = parse_value(val)
            # if our immediate parent on the stack is an active list item dictionary,
            # we insert keys directly into it rather than failing.
            if isinstance(parent, dict):
                parent[key] = val_obj
            else:
                raise ValueError('expected dict as parent')

            if val == '' and isinstance(val_obj, (dict, list)):
                stack.append((indent, val_obj, False))
    return root

#EOF
