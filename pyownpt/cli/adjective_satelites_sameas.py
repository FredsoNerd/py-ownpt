# -*- coding: utf-8 -*-

import sys
import argparse
import logging

logger = logging.getLogger()

from rdflib import Graph
from pyownpt.util import get_format
from pyownpt.repair import Repair

def _parse(args):
    ownpt_filapath = args.ownpt
    ownen_filapath = args.ownen
    sameas_filapath = args.sameas
    output_filepath = args.o

    # configs logging
    fileHandler = logging.FileHandler(filename="log-repair", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    adjective_satelites_uris(ownpt_filapath, ownen_filapath, sameas_filapath, output_filepath)


def adjective_satelites_uris(
    ownpt_filapath,
    ownen_filapath,
    sameas_filapath,
    output_filepath):

    # loading data
    
    logger.info(f"loading data from file '{ownpt_filapath}'")
    format = get_format(ownpt_filapath)
    ownpt = Graph().parse(ownpt_filapath, format=format)

    logger.info(f"loading data from file '{ownen_filapath}'")
    format = get_format(ownen_filapath)
    ownen = Graph().parse(ownen_filapath, format=format)

    logger.info(f"loading data from file '{sameas_filapath}'")
    format = get_format(sameas_filapath)
    sameas = Graph().parse(sameas_filapath, format=format)

    # formats into LMF format
    Repair(ownpt, lang=None).format_adjective_satelites_sameas(ownen, sameas)

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")
    output_format = get_format(output_filepath)
    ownpt.serialize(output_filepath, format=output_format)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("ownpt", help="own-pt-synsets file from ownpt")
parser.add_argument("ownen", help="own-en-synsets file from ownen")
parser.add_argument("sameas", help="own-pt-sameas file from ownpt")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())