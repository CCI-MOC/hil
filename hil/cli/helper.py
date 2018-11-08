"""Helper functions for the CLI live here"""
import json
import sys


def print_json(raw_output):
    """Format raw_output as json, print it and exit"""
    print(json.dumps(raw_output))
    sys.exit(0)

def gather_output(items, separator='\n'):
	"""Takes a list of <items> and returns a single string
	separated by <separator>
	"""
	returnee = ''
	for item in items:
		returnee += item + separator

	return returnee