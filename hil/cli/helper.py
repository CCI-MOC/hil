"""Helper functions for the CLI live here"""
import json
import sys
from prettytable import PrettyTable


def print_json(raw_output):
    """Format raw_output as json, print it and exit"""
    print(json.dumps(raw_output))
    sys.exit(0)


def gather_output(items, separator='\n'):
    """Takes a list of <items> and returns a single string
    separated by <separator>
    """
    return separator.join(items) + separator


def print_status_table(raw_output):
    """Print the networking action status ID in a PrettyTable"""
    status_table = PrettyTable()
    status_table.field_names = ['Field', 'Value']
    status_table.add_row(['Status ID', raw_output['status_id']])
    print(status_table)
    sys.exit(0)


def print_list_table(raw_output, header):
    """Prints a table with a single column. Also, puts the the counts
    of items in the column name.
    """
    count = str(len(raw_output))
    output_table = PrettyTable([header + ' (' + count + ')'])

    for item in raw_output:
        output_table.add_row([item])

    print(output_table)
    sys.exit(0)
