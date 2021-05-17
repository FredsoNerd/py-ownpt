# -*- coding: utf-8 -*-

import sys
import argparse
import logging
logger = logging.getLogger()

from json import loads
from rdflib import Graph

from pyownpt.repair import Repair


def _parse(args):
    ownpt_filapath = args.owp
    ownpt_format = args.fmt
    output_filepath = args.o
    output_format = args.f

    # configs logging
    fileHandler = logging.FileHandler(filename="log-repair", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    cli_repair_ownpt(ownpt_filapath=ownpt_filapath, ownpt_format=ownpt_format,
        output_filepath=output_filepath, output_format=output_format)
    

def cli_repair_ownpt(
    ownpt_filapath:str,
    ownpt_format:str="xml",
    output_filepath:str="output.xml",
    output_format:str="xml"):
    """"""

    logger.info(f"loading data from file '{ownpt_filapath}'")
    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)

    # repairs graph by rules
    Repair(ownpt).repair()

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")
    ownpt.serialize(output_filepath, format=output_format)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt")
parser.add_argument("fmt", help="own-pt rdf format (default: xml)", default="xml")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")
parser.add_argument("-f", help="output file format (default: xml)", default="xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())