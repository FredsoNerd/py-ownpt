# -*- coding: utf-8 -*-

import sys
import argparse
import logging
logger = logging.getLogger()

from rdflib import Graph
from rdflib.util import guess_format
from pyownpt.ownpt import OWNPT


def _parse(args):
    ownpt_filapath = args.owp
    ownen_filapath = args.owe
    output_filepath = args.o

    # configs logging
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler])

    # calls main function
    make_html(ownpt_filapath, ownen_filapath, output_filepath)


def make_html(ownpt_filapath, ownen_filapath, output_filepath):

    # loading data
    ownpt = Graph()

    logger.info(f"loading data from file '{ownpt_filapath}'")
    ownpt_format = _get_format(ownpt_filapath)
    ownpt.parse(ownpt_filapath, format=ownpt_format)

    logger.info(f"loading data from file '{ownen_filapath}'")
    ownen_format = _get_format(ownen_filapath)
    ownpt.parse(ownen_filapath, format=ownen_format)

    ownpt = OWNPT(ownpt)

    # create html
    logger.info(f"creating HTML")
    query = "SELECT ?ss ?lex ?lf1 ?lf2 WHERE { ?ss wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf1 ; wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf2 . ?ssen wn30:lexicographerFile ?lex ; owl:sameAs ?ss . FILTER ( !sameTerm(?lf1,?lf2) && sameTerm(ucase(?lf1),ucase(?lf2)) && str(?lf1) > str(?lf2)) } ORDER by ?ss ?lf1 "
    # query = "SELECT ?ss ?lf1 ?lf2 WHERE { ?ss wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf1 ; wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf2 . ?ssen wn30:lexicographerFile ?lex ; owl:sameAs ?ss . FILTER ( !sameTerm(?lf1,?lf2) && sameTerm(ucase(?lf1),ucase(?lf2)) && str(?lf1) > str(?lf2)) } ORDER by ?ss ?lf1 "
    # query = "SELECT ?ss ?lex ?lf1 ?lf2 WHERE { ?ss wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf1 ; wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf2 . ?ssen wn30:lexicographerFile ?lex ; owl:sameAs ?ss . FILTER ( !sameTerm(?lf1,?lf2) && sameTerm(ucase(?lf1),ucase(?lf2)) && str(?lf1) > str(?lf2)) } ORDER by ?ss ?lf1 "
    # query = "SELECT ?ss ?lf1 ?lf2 WHERE { ?ss wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf1 ; wn30:containsWordSense/wn30:word/wn30:lexicalForm ?lf2 . FILTER ( !sameTerm(?lf1,?lf2) && sameTerm(ucase(?lf1),ucase(?lf2)) && str(?lf1) > str(?lf2)) } ORDER by ?ss ?lf1 "

    count = 0
    output = "<table>"
    output += "<tr><td>synset id</td><td>lexfile</td><td>lexicalform1</td><td>lexicalform2</td><td>action</td></tr>"
    for ss, lex, lf1, lf2 in ownpt.graph.query(query):
        count += 1
        ss_id = ss.split('synset-')[-1]
        action = f"<a target='_blank' href='http://wn.mybluemix.net/synset?id={ss_id}'>go to {ss_id}</a>"
        output += f"<tr><td>{ss_id}</td><td>{lex.n3()}</td><td>{lf1.n3()}</td><td>{lf2.n3()}</td><td>{action}</td></tr>"
    output += "</table>"

    # serializes output
    logger.info(f"found {count} cases")
    logger.info(f"serializing output to '{output_filepath}'")
    open(output_filepath, "w").write(output)


def _get_format(filepath:str):
    """"""

    filepath_format = guess_format(filepath, {"jsonld":"json-ld"})    
    return filepath_format if filepath_format else filepath.split(".")[-1]


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("owp", help="rdf file from own-pt-morpho")
parser.add_argument("owe", help="rdf file from own-en-morpho")
parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())