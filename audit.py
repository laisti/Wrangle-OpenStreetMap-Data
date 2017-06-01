#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

filename = "sampleNYC.osm"

# patterns for potential problem values
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
direction_type_re = re.compile(r'^[e|E|w|W|s|S|n|N][\s|\.]', re.IGNORECASE)
height_type_re = re.compile('^[^.]*$')
housenumber_type_re = re.compile('(?!^\d+$)^.+$')
county_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# dictionary of correct street types
expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons"]

# dictionary of correct direction types
expected_direction_types = ["West", "East", "South", "North"]

# return all keys that consist of street
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street" or elem.attrib['k'] == "tiger:name_type" or elem.attrib['k'] == "tiger:name_type_1" or elem.attrib['k'] == "cityracks.street")

# return all keys that consist of postcode
def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")

# return all keys that consist of housenumber
def is_housenumber(elem):
    return (elem.attrib['k'] == "addr:housenumber" or elem.attrib['k'] == "cityracks.housenum")

# return all keys that consist of height
def is_height(elem):
    return (elem.attrib['k'] == "height" or elem.attrib['k'] == "min_height")

# find all potential problem street types and add them into dictionary
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected_street_types:
            street_types[street_type].add(street_name)

# find all potential problem direction types and add them into dictionary
def audit_direction_type(direction_types, direction_name):
    m = direction_type_re.search(direction_name)
    if m:
        direction_type = m.group()
        if direction_type not in expected_direction_types:
            direction_types[direction_type].add(direction_name)

# find all potential problem postcode types and add them into dictionary
def audit_postcode_type(postcode_types, postcode_key, postcode_value):
        postcode_types[postcode_key].add(postcode_value)

# find all potential problem housenumber types and add them into dictionary
def audit_housenumber_type(housenumber_types, housenumber):
    m = housenumber_type_re.search(housenumber)
    if m:
        housenumber_type = m.group()
        housenumber_types[housenumber_type].add(housenumber)

# find all potential problem height types and add them into dictionary
def audit_height_type(height_types, height):
    m = height_type_re.search(height)
    if m:
        height_type = m.group()
        height_types[height_type].add(height)

# go through every tag in the file, find nodes and ways tags, find all street, postcode, housenumber, height keys and add all their values to appropriate dictionaries
def audit(filename):
    osm_file = open(filename, "r")
    street_types = defaultdict(set)
    direction_types = defaultdict(set)
    postcode_types = defaultdict(set)
    height_types = defaultdict(set)
    housenumber_types = defaultdict(set)

    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                    audit_direction_type(direction_types, tag.attrib['v'])
                elif is_postcode(tag) and (tag.attrib['v'] < '10001' or tag.attrib['v'] > '11102'):
                    audit_postcode_type(postcode_types, tag.attrib['v'], tag.attrib['v'])
                elif is_housenumber(tag):
                    audit_housenumber_type(housenumber_types, tag.attrib['v'])
                elif is_height(tag):
                    audit_height_type(height_types, tag.attrib['v'])
    return street_types, direction_types, postcode_types, housenumber_types, height_types

street_types, direction_types, postcode_types, housenumber_types, height_types = audit(filename)
print "Potential wrong street types:"
pprint.pprint(dict(street_types))
print ""
print "Potential wrong direction types:"
pprint.pprint(dict(direction_types))
print ""
print "Potential wrong postcode types:"
pprint.pprint(dict(postcode_types))
print ""
print "Potential wrong housenumber types:"
pprint.pprint(dict(housenumber_types))
print ""
print "Potential wrong height types:"
pprint.pprint(dict(height_types))
