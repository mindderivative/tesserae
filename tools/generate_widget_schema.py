"""Writes the widget schema (`tesserae-widget-schema.json`), with the others: see `tools/generate_yaml_schema.py`, which this runs."""

import sys

import generate_yaml_schema

if __name__ == "__main__":
    sys.exit(generate_yaml_schema.main(sys.argv[1:]))
