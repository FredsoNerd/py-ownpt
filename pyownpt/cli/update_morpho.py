# -*- coding: utf-8 -*-

import argparse
import logging
logger = logging.getLogger(__name__)

from json import loads
from rdflib import Graph
from pyownpt.update import update_morpho_from_dump


def _parse(args):
    wn_filepath = args.wnd
    output_filepath = args.o
    output_format = args.f

    # call main function
    cli_update_morpho_from_dump(
        wn_filepath=wn_filepath,
        output_filepath=output_filepath,
        output_format=output_format)

def cli_update_morpho_from_dump(
    wn_filepath:str,
    output_filepath:str="output.xml",
    output_format:str="xml"):
    """"""

    doc_wn = [loads(line) for line in open(wn_filepath).readlines()]
    wn = [item["_source"] for item in doc_wn]

    morpho = update_morpho_from_dump(wn)

    # saves results
    morpho.serialize(output_filepath, format=output_format, encoding="utf8")


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("wnd", help="jsonl dump file wn.json")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")
parser.add_argument("-f", help="output file format (default: xml)", default="xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())