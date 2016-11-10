#!/usr/bin/env python3

import glob
import json

def nodupes(fields):
    fields = set()
    for field in fields:
        name = field['field_name']
        if name in fields:
            raise Exception("duplicate field: %s" % name)
        fields.add(name)

def qc(fname):
    with open(fname) as fd:
        data = json.load(fd)
        nodupes(data.get('dataset_fields', []))
        nodupes(data.get('resource_fields', []))

def main():
    for fname in glob.glob('*.json'):
        qc(fname)

if __name__ == '__main__':
    main()

