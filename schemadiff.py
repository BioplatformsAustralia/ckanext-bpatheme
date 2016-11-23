#!/usr/bin/env python

import json
import sys


def load_schema(path):
    with open(path) as fd:
        data = json.load(fd)
        dataset_fields = set([t['field_name'] for t in data['dataset_fields']])
        resource_fields = set([t['field_name'] for t in data['resource_fields']])
    return dataset_fields, resource_fields


def print_diff(topic, a, b):
    print("{} fields added:".format(topic))
    for f in (b - a):
        print("+ {}".format(f))
    print("{} fields removed:".format(topic))
    for f in (a - b):
        print("- {}".format(f))
    
def main():
    f1, f2 = sys.argv[1:]
    d1, r1 = load_schema(f1)
    d2, r2 = load_schema(f2)
    print_diff("dataset", d1, d2)
    print_diff("resource", r1, r2)

if __name__ == '__main__':
    main()

