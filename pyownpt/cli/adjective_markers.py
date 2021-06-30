# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging

from rdflib.graph import ConjunctiveGraph
logger = logging.getLogger()

from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.repair import Repair


def _parse(args):
    sense_filapath = args.sen
    synset_filapath = args.syn
    adj_filepath = args.adj
    output_filepath = args.o

    # configs logging
    fileHandler = logging.FileHandler(filename="log-adjmarkers", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    adjective_markers(sense_filapath, synset_filapath, adj_filepath, output_filepath)
    

def adjective_markers(
    sense_filapath:str,
    synset_filapath:str,
    adj_filepath:str,
    output_filepath:str="output.xml"):
    """"""
    
    logger.info(f"loading data from file '{sense_filapath}'")
    format = _get_format(sense_filapath)
    senses = Graph().parse(sense_filapath, format=format)

    logger.info(f"loading data from file '{synset_filapath}'")
    format = _get_format(synset_filapath)
    synsets = Graph().parse(synset_filapath, format=format)
    
    ownpt = senses + synsets
    
    logger.info(f"loading data from file '{adj_filepath}'")
    adjective_lines = open(adj_filepath).readlines()
    adjective_lines = [a for a in adjective_lines if not a.startswith(" ")]

    # repairs graph by rules
    Repair(ownpt, lang="en").add_adjective_markers(senses, adjective_lines)

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")
    output_format = _get_format(output_filepath)
    senses.serialize(output_filepath, format=output_format)


def _get_format(filepath:str):
    """"""

    filepath_format = guess_format(filepath, {"jsonld":"json-ld"})    
    return filepath_format if filepath_format else filepath.split(".")[-1]


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("sen", help="wordsense file from own-en")
parser.add_argument("syn", help="synsets file from own-en")
parser.add_argument("adj", help="data.adj file from pwn")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())