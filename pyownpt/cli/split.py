# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging

logger = logging.getLogger()

from rdflib import Graph
from pyownpt.util import get_format
from pyownpt.split import Split


def _parse(args):
    own_filapaths = args.owp
    lang = args.l
    extension = args.e
    output_filepath = args.o

    # configs logging
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler])

    # calls main function
    split_into_files(own_filapaths, lang, extension, output_filepath)


def split_into_files(
    ownpt_filapaths:str, 
    lang:str,
    extension:str,
    output_filepath:str):

    # loading data
    ownpt = Graph()
    for ownpt_filapath in ownpt_filapaths:
        logger.info(f"loading data from file '{ownpt_filapath}'")
        ownpt_format = get_format(ownpt_filapath)
        ownpt.parse(ownpt_filapath, format=ownpt_format)
      
    # generates files
    os.makedirs(output_filepath, exist_ok=True)

    ## generates files
    logger.info(f"generating splitted graphs")
    split = Split(ownpt, lang)

    actions = [
        (split.pop_morphosemantic_links, "morphosemantic-links"),
        (split.pop_same_as, "same-as"),
        (split.pop_relations, "relations"),
        (split.pop_words, "words"),
        (split.pop_wordsenses, "wordsenses"),
        (split.pop_base_synsets, "synsets"),]

    for action, name in actions:
        filename = f"own-{lang}-{name}.{extension}"
        outfile = os.path.join(output_filepath, filename)
        logger.info(f"split graph to file '{outfile}'")
        action().serialize(outfile, format=get_format(outfile))


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="files from own-pt", nargs="+")
parser.add_argument("-l", help="wordnet language (default: 'pt')", default="pt")
parser.add_argument("-e", help="splitted extension (default: 'ttl')", default="ttl")
parser.add_argument("-o", help="output filepath (default: 'output')", default="output")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())