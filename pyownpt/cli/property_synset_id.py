# -*- coding: utf-8 -*-

import sys
import argparse
import logging

logger = logging.getLogger()

from rdflib import Graph
from pyownpt.util import get_format
from pyownpt.repair import Repair

def _parse(args):
    ownpt_filapaths = args.owp
    lang = args.l
    output_filepath = args.o

    # configs logging
    fileHandler = logging.FileHandler(filename="log-repair", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    property_synset_id(ownpt_filapaths, lang, output_filepath)


def property_synset_id(
    ownpt_filapaths,
    lang,
    output_filepath):

    # loading data
    ownpt = Graph()
    for ownpt_filapath in ownpt_filapaths:
        logger.info(f"loading data from file '{ownpt_filapath}'")
        ownpt_format = get_format(ownpt_filapath)
        ownpt.parse(ownpt_filapath, format=ownpt_format)

    # formats into LMF format
    Repair(ownpt, lang=lang).format_synset_id()

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")
    output_format = get_format(output_filepath)
    ownpt.serialize(output_filepath, format=output_format)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="files from own-pt", nargs="+")
parser.add_argument("-l", help="lang (default: 'en')", default="en")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())