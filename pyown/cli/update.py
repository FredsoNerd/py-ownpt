# -*- coding: utf-8 -*-

import sys
import argparse
import logging

logger = logging.getLogger()

from json import loads
from rdflib import Graph
from pyown.repair import Repair
from pyown.update import Update
from pyown.compare import Compare
from pyown.util import get_format, get_unify_actions


def _parse(args):
    filapaths = args.rdf
    wn_filepaths = args.wns
    votes_filepaths = args.vts
    suggestions_filepaths = args.sgs

    # config
    lang = args.l
    users_senior = args.u
    output_filepath = args.o
    trashold_senior = args.ts
    trashold_junior = args.tj

    # sets logging
    fileHandler = logging.FileHandler(filename="log-update", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # cals main function
    cli_update_own_from_dump(filapaths, wn_filepaths,
        suggestions_filepaths, votes_filepaths, output_filepath,
        lang, users_senior, trashold_senior, trashold_junior)


def cli_update_own_from_dump(
    filapaths:str,
    wn_filepaths:str,
    suggestions_filepaths:str,
    votes_filepaths:str, 
    output_filepath:str,
    lang:str,
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2):
    """"""

    # loading graph
    rdf = Graph()
    for filapath in filapaths:
        logger.info(f"loading data from '{filapath}'")
        format = get_format(filapath)
        rdf.parse(filapath, format=format)

    # loads the data
    doc_wn = []
    for wn_filepath in wn_filepaths:
        logger.info(f"loading data from '{wn_filepath}'")
        doc_wn += [loads(line) for line in open(wn_filepath).readlines()]
    
    doc_votes = []
    for votes_filepath in votes_filepaths:
        logger.info(f"loading data from '{votes_filepath}'")
        doc_votes += [loads(line) for line in open(votes_filepath).readlines()]

    doc_suggestions = []
    for suggestions_filepath in suggestions_filepaths:
        logger.info(f"loading data from '{suggestions_filepath}'")
        doc_suggestions += [loads(line) for line in open(suggestions_filepath).readlines()]

    # downgrades match given dump Wn
    if doc_wn:
        logger.info(f"comparing wordnet to dump Wn")
        report = Compare(rdf, doc_wn).compare_items()
        actions = get_unify_actions(report)
    
        logger.info(f"applying actions from Comparing")
        Update(rdf, lang).update_from_compare(actions)

    # updates given Suggesstions and Votes
    if doc_votes and doc_suggestions:
        logger.info(f"applying actions from Suggestions")
        Update(rdf, lang).update(doc_suggestions,
            doc_votes, users_senior, trashold_senior, trashold_junior)
    
    # validates and repaires resulting
    repair = Repair(rdf, lang)
    logger.info(f"applying repairing actions to Wordnet")
    repair.repair_words()
    logger.info(f"granting well ordered Sense instances") 
    repair.sort_senses_instances()

    # saves results
    logger.info(f"serializing results to '{output_filepath}'")
    format = get_format(output_filepath)
    rdf.serialize(output_filepath, format=format)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("rdf", help="rdf files", nargs="+")
parser.add_argument("--wns", help="file wn.jsonl", nargs="+", default=[])
parser.add_argument("--vts", help="file votes.jsonl", nargs="+", default=[])
parser.add_argument("--sgs", help="file suggestions.jsonl", nargs="+", default=[])

parser.add_argument("-l", help="wordnet lang")
parser.add_argument("-u", help="list of senior/proficient users", nargs="*", default=[])
parser.add_argument("-ts", help="senior suggestion score trashold (default: 1)", default=1)
parser.add_argument("-tj", help="junior suggestion score trashold (default: 2)", default=2)
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())