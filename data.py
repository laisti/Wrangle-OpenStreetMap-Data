#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema

filename = "sampleNYC.osm"

# CSV files to where we import cleaned data
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# patterns for problem values
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
direction_type_re = re.compile(r'^[e|E|w|W|s|S|n|N][\s|\.]', re.IGNORECASE)
housenumber_type_re = re.compile('(?!^\d+$)^.+$')
height_type_re = re.compile('^[^.]*$')
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# CSV columns
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# dictionary of the correct street values
mapping_street = {"ave": "Avenue",
                  "Ave": "Avenue",
                  "Blvd": "Boulevard",
                  "Brg": "Bridge",
                  "Dr": "Drive",
                  "Expy": "Expressway",
                  "Pky": "Parkway",
                  "Pl": "Place",
                  "Plz": "Plaza",
                  "Rd": "Road",
                  "S": "South",
                  "Sq": "Square",
                  "St": "Street",
                  "Ter": "Terrace"}

# dictioanry of the correct direction values
mapping_direction = {"E": "East",
                     "E.": "East",
                     "W": "West"}

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

# find all problem street types and change their values to correct from the mapping dictionary
def update_streets(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping_street.keys():
            name = re.sub(street_type, mapping_street[street_type], name)
    return name

# find all problem direction types and change their values to correct from the mapping dictionary
def update_directions(name, mapping):
    m = direction_type_re.search(name)
    if m:
        direction_type = m.group()
        if direction_type in mapping_direction.keys():
            name = re.sub(direction_type, mapping_direction[direction_type], name)
    return name

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    for tag in element.iter('tag'):
        key = tag.attrib['k']
        value = tag.attrib['v']

        # if a tag "k" value contains problematic characters, it should be ignored
        if problem_chars.search(key):
            continue

        # cleaning street names
        if is_street_name(tag):
            # updating problem values with defined in mapping dictionary
            value = update_streets(value, mapping_street)

        # cleaning direction names
        if is_street_name(tag):
            value = update_directions(value, mapping_direction)

        # cleaning postcodes
        if is_postcode(tag) and (value < '10001' or value > '11102'):
            value = '10001'

        # cleaning house numbers
        if is_housenumber(tag):
            m = housenumber_type_re.search(value)
            if m:
                if re.search(r"\s", value):
                    value = value.split(" ")[0]
                    if re.search(r"\;", value):
                        value = value.split(";")[0]
                elif re.search(r"\-", value):
                    value = value.split("-")[0]
                elif re.search(r"[^a-zA-Z]", value):
                    value = value[:-1]

        # cleaning height values
        if is_height(tag):
            m = height_type_re.search(value)
            if m:
                value = ''.join((value,'.0'))

        # create temporary dictionary for 'tag'
        tag_dummy = {}
        tag_dummy['id'] = element.attrib['id']
        tag_dummy['key'] = key
        tag_dummy['type'] = default_tag_type
        tag_dummy['value'] = value

        if LOWER_COLON.search(key):
            key_list = key.split(":")
            tag_dummy['type'] =  key_list.pop(0)
            tag_dummy['key'] = ":".join(key_list)

        tags.append(tag_dummy)

    if element.tag == 'node':
        for node_attr_field in node_attr_fields:
            node_attribs[node_attr_field] = element.attrib[node_attr_field]
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for way_attr_field in way_attr_fields:
            way_attribs[way_attr_field] = element.attrib[way_attr_field]
        counter = -1
        # iterating through the nd tags to get refs
        for nd_tag in element.iter('nd'):
            counter += 1
            nd_dummy = {}
            nd_dummy['id'] = element.attrib['id']
            nd_dummy['node_id'] = nd_tag.attrib['ref']
            nd_dummy['position'] = counter
            way_nodes.append(nd_dummy)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(filename, validate=True)
