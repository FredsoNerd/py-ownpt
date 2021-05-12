# -*- coding: utf-8 -*-

import sys
import argparse
import logging
logger = logging.getLogger()

from json import loads, dump
from rdflib import Graph
from pyownpt.compare import Compare


def _parse(args):
    ownpt_filapath = args.owp
    wn_filepath = args.wnd
    ownpt_format = args.fmt
    output_filepath = args.o

    # sets verbosity level
    fileHandler = logging.FileHandler(filename="log", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    cli_compare_ownpt_dump(ownpt_filapath, wn_filepath, ownpt_format, output_filepath)
    

def cli_compare_ownpt_dump(
    ownpt_filapath:str,
    wn_filepath:str,
    ownpt_format:str="nt",
    output_filepath:str = "output.json"):
    """"""

    logger.info(f"loading data from file '{ownpt_filapath}'")
    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)

    logger.info(f"loading data from file '{wn_filepath}'")
    wn = [loads(line)["_source"] for line in open(wn_filepath).readlines()]
    
    # create and apply compare
    compare = Compare(ownpt, wn)

    _, _ = compare.compare_item_ownpt_dump(item_name="word_pt")
    _, _ = compare.compare_item_ownpt_dump(item_name="gloss_pt")
    _, _ = compare.compare_item_ownpt_dump(item_name="example_pt")

    # makes json where docs differ
    report_words["docs"]
    for doc, doc_report in report_words["docs"].copy().items():
        if doc_report["compare"]:
            # removes if comparing positive
            report_words["docs"].pop(doc)
        else:
            # adds actions to apply
            report_words["docs"][doc]["add-word-pt"] = []
            report_words["docs"][doc]["remove-word-pt"] = []
    
    # serializes to output
    logger.warning(f"serializing report to {output_filepath}")
    dump(report_words, open(output_filepath, mode="w"))


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt")
parser.add_argument("wnd", help="jsonl dump file wn.json")
parser.add_argument("fmt", help="own-pt rdf format (default: xml)", default="xml")
parser.add_argument("-o", help="output file (default: output.json)", default="output.json")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())