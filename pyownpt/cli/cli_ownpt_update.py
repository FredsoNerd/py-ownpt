# -*- coding: utf-8 -*-

import argparse
import logging
logger = logging.getLogger(__name__)

from json import loads
from rdflib import Graph
from pyownpt.update import update_ownpt_from_dump


def _parse(args):
    ownpt_filapath = args.owp
    wn_filepath = args.wnd
    ownpt_format = args.fmt
    output_filepath = args.o
    output_format = args.f

    cli_update_ownpt_from_dump(ownpt_filapath, wn_filepath,
        ownpt_format, output_filepath, output_format)

def cli_update_ownpt_from_dump(
    ownpt_filapath:str,
    wn_filepath:str,
    ownpt_format:str="nt",
    output_filepath:str="output.xml",
    output_format:str="xml"):
    """"""

    doc_wn = [loads(line) for line in open(wn_filepath).readlines()]
    wn = [item["_source"] for item in doc_wn]

    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)
    update_ownpt_from_dump(ownpt, wn)

    # saves results
    ownpt.serialize(output_filepath, format=output_format, encoding="utf8")


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt")
parser.add_argument("wnd", help="jsonl dump file wn.json")
parser.add_argument("fmt", help="own-pt rdf format (default: xml)", default="xml")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")
parser.add_argument("-f", help="output file format (default: xml)", default="xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())