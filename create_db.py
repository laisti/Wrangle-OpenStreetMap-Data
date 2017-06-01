#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import sqlite3

filename = "OpenStreetMap_NYC.db"

# source CSV files
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# connect to database
db = sqlite3.connect(filename)
cur = db.cursor()


# create a nodes table
cur.execute("""CREATE TABLE IF NOT EXISTS nodes(
                                id INTEGER primary key,
                                lat REAL,
                                lon REAL,
                                user INTEGER,
                                uid TEXT,
                                version TEXT,
                                changeset INTEGER,
                                timestamp TEXT
                                );""")

# create a nodes_tags table
cur.execute("""CREATE TABLE IF NOT EXISTS nodes_tags(
                                id INTEGER references nodes(id),
                                key TEXT,
                                value TEXT,
                                type TEXT
                                );""")

# create a ways table
cur.execute("""CREATE TABLE IF NOT EXISTS ways(
                                id INTEGER primary key,
                                user INTEGER,
                                uid TEXT,
                                version TEXT,
                                changeset INTEGER,
                                timestamp TEXT
                                );""")

# create a ways_nodes table
cur.execute("""CREATE TABLE IF NOT EXISTS ways_nodes(
                                id INTEGER references ways(id),
                                node_id INTEGER references nodes(id),
                                position INTEGER
                                );""")

# create a ways_tags table
cur.execute("""CREATE TABLE IF NOT EXISTS ways_tags(
                                id INTEGER references ways(id),
                                key TEXT,
                                value TEXT,
                                type TEXT
                                );""")

# import data from CSV files to appropriate tables in SQL database
# nodes
with open(NODES_PATH,'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    to_db = [(i['id'], i['lat'],i['lon'], i['user'].decode("utf-8"), i['uid'], i['version'], i['changeset'], i['timestamp']) for i in reader]
cur.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db)
# save changes into db
db.commit()

# nodes_tags
with open(NODE_TAGS_PATH,'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    to_db = [(i['id'], i['key'].decode("utf-8"),i['value'].decode("utf-8"), i['type'].decode("utf-8")) for i in reader]
cur.executemany("INSERT INTO nodes_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db)
# save changes into db
db.commit()

# ways
with open(WAYS_PATH,'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    to_db = [(i['id'], i['user'].decode("utf-8"),i['uid'], i['version'], i['changeset'], i['timestamp']) for i in reader]
cur.executemany("INSERT INTO ways(id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db)
# save changes into db
db.commit()

# ways_nodes
with open(WAY_NODES_PATH,'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    to_db = [(i['id'], i['node_id'], i['position']) for i in reader]
cur.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db)
# save changes into db
db.commit()

# ways_tags
with open(WAY_TAGS_PATH,'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    to_db = [(i['id'], i['key'].decode("utf-8"), i['value'].decode("utf-8"), i['type'].decode("utf-8")) for i in reader]
cur.executemany("INSERT INTO ways_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db)
# save changes into db
db.commit()
