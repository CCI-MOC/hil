"""Helper functions for the CLI live here"""
import json
import sys
import os
from prettytable import PrettyTable

try:
    HIL_TIMEOUT = int(os.getenv('HIL_TIMEOUT', 10))
except ValueError:
    sys.exit("Please set environment variable HIL_TIMEOUT to a number")


def print_json(raw_output):
    """Format raw_output as json, print it and exit"""
    print(json.dumps(raw_output))
    sys.exit(0)


def make_table(field_names, rows):
    """Generate a PrettyTable and return it.
    If there's only field, then it will add the count of items in the header.
    """
    if len(field_names) == 1:
        field_names = [field_names[0] + ' (' + str(len(rows)) + ')']

    output_table = PrettyTable(field_names)
    for row in rows:
        output_table.add_row(row)
    return output_table
