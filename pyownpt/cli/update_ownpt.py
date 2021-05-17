# -*- coding: utf-8 -*-

from re import U
import sys
import argparse
import logging
logger = logging.getLogger()

from json import loads
from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.update import Update


def _parse(args):
    ownpt_filapath = args.owp
    suggestions_filepath = args.sgs
    votes_filepath = args.vts
    output_filepath = args.o
    users_senior = args.u
    trashold_senior = args.ts
    trashold_junior = args.tj
    actions_filepath = args.a

    # sets logging
    fileHandler = logging.FileHandler(filename="log-update", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # cals main function
    cli_update_ownpt_from_dump(ownpt_filapath, suggestions_filepath, votes_filepath,
        output_filepath, users_senior, trashold_senior, trashold_junior, actions_filepath)


def cli_update_ownpt_from_dump(
    ownpt_filapath:str,
    suggestions_filepath:str,
    votes_filepath:str, 
    output_filepath:str="output.xml",
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2,
    actions_filepath:str=None):
    """"""

    # loads the data
    logger.info(f"loading data from '{votes_filepath}'")
    doc_votes = [loads(line) for line in open(votes_filepath).readlines()]

    logger.info(f"loading data from '{suggestions_filepath}'")
    doc_suggestions = [loads(line) for line in open(suggestions_filepath).readlines()]

    actions = None
    if actions_filepath is not None:
        logger.info(f"loading data from '{actions_filepath}'")
        actions = loads(open(actions_filepath).read())

    # loading graph
    logger.info(f"loading data from '{ownpt_filapath}'")
    ownpt_format = _get_format(ownpt_filapath)
    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)
    
    # updates graph
    update = Update(ownpt)

    if actions is not None:
        logger.info(f"applying actions from Comparing")
        update.update_from_compare(actions)

    logger.info(f"applying actions from Suggestions")
    Update(ownpt).update(doc_suggestions, doc_votes,
        users_senior, trashold_senior, trashold_junior)

    # saves results
    logger.info(f"serializing results to '{output_filepath}'")
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
parser.add_argument("sgs", help="file suggestions.json")
parser.add_argument("vts", help="file votes.json")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")
parser.add_argument("-u", help="list of senior/proficient users", nargs="*", default=[])
parser.add_argument("-ts", help="senior suggestion score trashold (default: 1)", default=1)
parser.add_argument("-tj", help="junior suggestion score trashold (default: 2)", default=2)
parser.add_argument("-a", help="annotated file with actions to be applied", default=None)

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())