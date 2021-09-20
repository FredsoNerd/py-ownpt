# -*- coding: utf-8 -*-

import sys
import argparse
import logging

logger = logging.getLogger()

from rdflib import Graph
from pyown.util import get_format
from pyown.lmf import LMF


def _parse(args):
    filapaths = args.rdf
    ili_map_filapath = args.ili
    output_filepath = args.o

    # basic config
    label = args.lb
    lang = args.lg
    status = args.status
    version = args.vr
    lexicon_id = args.li
    confidenceScore = args.cs
    
    url = args.url
    email = args.email
    license = args.licence
    citation = args.citation
    
    # configs logging
    fileHandler = logging.FileHandler(filename="log-format", mode="w")
    fileHandler.setLevel(logging.DEBUG)
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler,fileHandler])

    # calls main function
    lmf_format(filapaths, ili_map_filapath, output_filepath, lexicon_id,  label,
        version, lang, status, confidenceScore, url, email, license, citation)


def lmf_format(
    filapaths:str,
    ili_map_filapath:str,
    output_filepath:str,
    lexicon_id:str,
    label:str,
    version:str,
    lang:str,
    status:str,
    confidence_score:str,
    url:str,
    email,
    license,
    citation):

    # loading data
    rdf = Graph()
    for filapath in filapaths:
        logger.info(f"loading data from file '{filapath}'")
        format = get_format(filapath)
        rdf.parse(filapath, format=format)

    ili_map = Graph()
    logger.info(f"loading data from file '{ili_map_filapath}'")
    ili_map_format = get_format(ili_map_filapath)
    ili_map.parse(ili_map_filapath, format=ili_map_format)

    # formats into LMF format
    logger.info(f"formatting into LMF format")
    lmf = LMF(rdf, ili_map, lexicon_id, label, version, lang, status,
            confidence_score, url, email, license, citation).format()

    # serializes output
    logger.info(f"serialiing output to {output_filepath}")
    open(output_filepath, "w", encoding="utf8").write(lmf)


# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("rdf", help="rdf files", nargs="+")
parser.add_argument("ili", help="rdf file from ili-map")

parser.add_argument("-o", help="output file (default: output.xml)", default="output.xml")

parser.add_argument("-li", help="lexicon_id")
parser.add_argument("-lb", help="label")
parser.add_argument("-vr", help="version")
parser.add_argument("-lg", help="language")
parser.add_argument("-cs", help="confidence score")
parser.add_argument("--url", help="projct url")
parser.add_argument("--email", help="responsible")
parser.add_argument("--status", help="project status")
parser.add_argument("--licence", help="project licence")
parser.add_argument("--citation", help="project citation")


parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())