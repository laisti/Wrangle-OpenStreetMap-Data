#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import pprint
import re

filename = "sampleNYC.osm"

# patterns for values
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
lower_dot = re.compile(r'^([a-z]|_)*.([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# count values which are matched to patterns
def key_type(element, keys):
    if element.tag == "tag":
        key = element.attrib['k']
        if re.search(lower, key) != None:
            keys['lower'] += 1
        elif re.search(lower_colon, key) != None:
            keys['lower_colon'] += 1
        elif re.search(lower_dot, key) != None:
            keys['lower_dot'] += 1
        elif re.search(problemchars, key) != None:
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "lower_dot": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    return keys

keys = process_map(filename)
pprint.pprint(keys)