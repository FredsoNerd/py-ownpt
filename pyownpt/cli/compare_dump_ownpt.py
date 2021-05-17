# -*- coding: utf-8 -*-

import sys
import argparse
import logging
logger = logging.getLogger()

from json import loads, dump
from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.compare import Compare


def _parse(args):
    ownpt_filapath = args.owp
    wn_filepath = args.wnd
    morpho_filapath = args.m
    output_filepath = args.o

    # sets verbosity level
    fileHandler = logging.FileHandler(filename="log-compare", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    cli_compare_ownpt_dump(ownpt_filapath, wn_filepath, morpho_filapath, output_filepath)
    

def cli_compare_ownpt_dump(
    ownpt_filapath:str,
    wn_filepath:str,
    morpho_filapath:str,
    output_filepath:str = "output.json"):
    """"""

    ownpt = Graph()

    logger.info(f"loading data from file '{ownpt_filapath}'")
    ownpt_format = _get_format(ownpt_filapath)
    ownpt.parse(ownpt_filapath, format=ownpt_format)

    if morpho_filapath:
        logger.info(f"loading data from file '{morpho_filapath}'")
        morpho_format = _get_format(morpho_filapath)
        ownpt.parse(morpho_filapath, format=morpho_format)

    logger.info(f"loading data from file '{wn_filepath}'")
    wn = [loads(line)["_source"] for line in open(wn_filepath).readlines()]
    
    # create and apply compare
    compare = Compare(ownpt, wn)
    report = compare.compare_items()
    compare.compare_antonymof_ownpt_dump()
    if morpho_filapath:
        compare.compare_morpho_ownpt_dump()

    # makes json where docs differ
    for doc, doc_report in report.copy().items():
        if doc_report["compare"]:
            # removes if comparing positive
            report.pop(doc)
        else:
            # adds actions to apply to ownpt
            report[doc]["actions"] = {
                "add-word-pt": report[doc]["word_pt"]["dump"],
                "remove-word-pt": report[doc]["word_pt"]["ownpt"],
                "add-gloss-pt": report[doc]["gloss_pt"]["dump"],
                "remove-gloss-pt": report[doc]["gloss_pt"]["ownpt"],
                "add-example-pt": report[doc]["example_pt"]["dump"],
                "remove-example-pt": report[doc]["example_pt"]["ownpt"]}
    
    # serializes to output
    logger.warning(f"serializing report to '{output_filepath}'")
    dump(report, open(output_filepath, mode="w"), ensure_ascii=False)


def _get_format(filepath:str):
    """"""

    filepath_format = guess_format(filepath, {"jsonld":"json-ld"})
    return filepath_format if filepath_format else filepath.split(".")[-1]


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt")
parser.add_argument("wnd", help="jsonl dump file wn.json")
parser.add_argument("-m", help="compare morphosemantic-liks-pt")
parser.add_argument("-o", help="output file (default: output.json)", default="output.json")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())