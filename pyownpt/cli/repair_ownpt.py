# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
logger = logging.getLogger()

from json import loads
from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.repair import Repair


def _parse(args):
    ownpt_filapath = args.owp
    output_filepath = args.o

    # configs logging
    fileHandler = logging.FileHandler(filename="log-repair", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    cli_repair_ownpt(ownpt_filapath=ownpt_filapath, output_filepath=output_filepath)
    

def cli_repair_ownpt(
    ownpt_filapath:str,
    output_filepath:str="output.xml"):
    """"""

    logger.info(f"loading data from file '{ownpt_filapath}'")
    ownpt_format = _get_format(ownpt_filapath)
    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)

    # repairs graph by rules
    Repair(ownpt).repair()

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")
    output_format = _get_format(output_filepath)
    ownpt.serialize(output_filepath, format=output_format)


def _get_format(filepath:str):
    """"""

    filepath_format = guess_format(filepath, {"jsonld":"json-ld"})    
    return filepath_format if filepath_format else filepath.split(".")[-1]


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())