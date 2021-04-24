# -*- coding: utf-8 -*-

import argparse
import logging
logger = logging.getLogger(__name__)

from json import loads, dump
from pyownpt.update import dump_update

def _parse(args):
    wn_filepath = args.wn
    suggestions_filepath = args.sg
    votes_filepath = args.vt
    output_filepath = args.o
    users_senior = args.u
    trashold_senior = args.ts
    trashold_junior = args.tj

    # calls the main function
    _cli_dump_update(wn_filepath, suggestions_filepath, votes_filepath,
        output_filepath, users_senior, trashold_senior, trashold_junior)


def _cli_dump_update(
    wn_filepath:str,
    suggestions_filepath:str,
    votes_filepath:str,
    output_filepath:str,
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2):
    """"""

    # loads the data    
    doc_wn = [loads(line) for line in open(wn_filepath).readlines()]
    doc_votes = [loads(line) for line in open(votes_filepath).readlines()]
    doc_suggestions = [loads(line) for line in open(suggestions_filepath).readlines()]

    # updates wn docs
    dump_update(doc_wn, doc_suggestions, doc_votes, users_senior, trashold_senior, trashold_junior)

    # saves results as jsonl
    outfile = open(output_filepath, "w")
    for item in doc_wn:
        dump(item, outfile)
        outfile.write("\n")


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("wn", help="file wn.json")
parser.add_argument("sg", help="file suggestions.json")
parser.add_argument("vt", help="file votes.json")
parser.add_argument("-o", help="output file (default: output.jsonl)", default="output.jsonl")
parser.add_argument("-u", help="list of senior/proficient users (default: [])", default=[])
parser.add_argument("-ts", help="senior suggestion score trashold (default: 1)", default=1)
parser.add_argument("-tj", help="junior suggestion score trashold (default: 2)", default=2)

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# sets verbosity level
logging.basicConfig(level= 30-10*parser.parse_args()["v"])

# cals the parser
_parse(parser.parse_args())