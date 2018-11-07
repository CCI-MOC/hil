"""Helper functions for the CLI live here"""
import json
import sys


def print_json(raw_output):
    """Format raw_output as json, print it and exit"""
    print(json.dumps(raw_output))
    sys.exit(0)
