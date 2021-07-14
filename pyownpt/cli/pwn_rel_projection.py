# -*- coding: utf-8 -*-

import sys
import argparse
import logging
logger = logging.getLogger()

from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.project import ProjectRelations


def _parse(args):
    ownpt_filapaths = args.owp
    ownen_filapaths = args.pwn
    output_filepath = args.o

    # configs logging
    fileHandler = logging.FileHandler(filename="log-project", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    project_relations(ownpt_filapaths, ownen_filapaths, output_filepath)
    

def project_relations(
    ownpt_filapaths:str,
    ownen_filapaths:str,
    output_filepath:str="output.xml"):
    """"""
    
    ownpt = Graph()
    for ownpt_filapath in ownpt_filapaths:
        logger.info(f"loading data from file '{ownpt_filapath}'")
        format = guess_format(ownpt_filapath)
        ownpt.parse(ownpt_filapath, format=format)

    ownen = Graph()
    for ownen_filapath in ownen_filapaths:
        logger.info(f"loading data from file '{ownen_filapath}'")
        format = guess_format(ownen_filapath)
        ownen.parse(ownen_filapath, format=format)

    # project relations
    ProjectRelations(ownpt, ownen).project()

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")
    output_format = guess_format(output_filepath)
    ownpt.serialize(output_filepath, format=output_format)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf files from wordnet", nargs="+")
parser.add_argument("--pwn", help="rdf files from wordnet", nargs="+")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())