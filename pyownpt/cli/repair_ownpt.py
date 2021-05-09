# -*- coding: utf-8 -*-

import argparse
import logging
logger = logging.getLogger()

from json import loads
from rdflib import Graph

from pyownpt.repair import fix_word_blank_nodes
from pyownpt.repair import fix_sense_blank_nodes
from pyownpt.repair import add_sense_labels
from pyownpt.repair import remove_void_words
from pyownpt.repair import expand_sense_words
from pyownpt.repair import add_word_types
from pyownpt.repair import add_sense_types
from pyownpt.repair import remove_word_duplicates
from pyownpt.repair import remove_sense_duplicates

def _parse(args):
    ownpt_filapath = args.owp
    ownpt_format = args.fmt
    output_filepath = args.o
    output_format = args.f

    # sets verbosity level
    logging.basicConfig(level= 30-10*args.v)

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

    # replacing blank nodes
    fix_word_blank_nodes(ownpt)
    fix_sense_blank_nodes(ownpt)
    # removing void words
    remove_void_words(ownpt)
    # words to senses by label
    expand_sense_words(ownpt)
    # add labels to senses
    add_sense_labels(ownpt)
    # type Words and WordSenses
    add_word_types(ownpt)
    add_sense_types(ownpt)
    # removing duplicates
    remove_word_duplicates(ownpt)
    remove_sense_duplicates(ownpt)


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