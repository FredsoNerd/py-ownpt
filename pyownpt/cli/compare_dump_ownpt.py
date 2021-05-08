# -*- coding: utf-8 -*-

import sys
import argparse
import logging
logger = logging.getLogger()

from json import loads
from rdflib import Graph
from pyownpt.compare import compare_ownpt_dump


def _parse(args):
    ownpt_filapath = args.owp
    wn_filepath = args.wnd
    ownpt_format = args.fmt

    # sets verbosity level
    logging.basicConfig(stream=sys.stdout, level= 30-10*args.v)

    # calls main function
    cli_compare_ownpt_dump(ownpt_filapath, wn_filepath, ownpt_format)
    

def cli_compare_ownpt_dump(
    ownpt_filapath:str,
    wn_filepath:str,
    ownpt_format:str="nt"):
    """"""

    logger.info(f"loading data from file '{ownpt_filapath}'")
    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)

    logger.info(f"loading data from file '{wn_filepath}'")
    wn = [loads(line)["_source"] for line in open(wn_filepath).readlines()]
    
    _, report_words, _, report_anto = compare_ownpt_dump(ownpt, wn)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt")
parser.add_argument("wnd", help="jsonl dump file wn.json")
parser.add_argument("fmt", help="own-pt rdf format (default: xml)", default="xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())