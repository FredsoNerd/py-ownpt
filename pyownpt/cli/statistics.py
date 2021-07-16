# -*- coding: utf-8 -*-

from six import with_metaclass
from pyownpt.ownpt import OWNPT
import sys
import argparse
import logging
import tabulate

logger = logging.getLogger()

from rdflib import Graph
from pyownpt.util import get_format
from pyownpt.statistics import Statistics

def _parse(args):
    ownpt_filapaths = args.ownpt
    ownen_filapaths = args.ownen
    output_filepath = args.o

    # configs logging
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setLevel(level=30-10*args.v)

    logging.basicConfig(level=logging.DEBUG, handlers=[streamHandler])

    # calls main function
    statistics(ownpt_filapaths, ownen_filapaths, output_filepath)


def statistics(
    ownpt_filapaths,
    ownen_filapaths,
    output_filepath):

    # loading data
    ownpt = Graph()
    for filapath in ownpt_filapaths:
        logger.info(f"loading data from file '{filapath}'")
        format = get_format(filapath)
        ownpt.parse(filapath, format=format)

    ownen = Graph()
    for filapath in ownen_filapaths:
        logger.info(f"loading data from file '{filapath}'")
        format = get_format(filapath)
        ownen.parse(filapath, format=format)

    # generates statistics
    ## pt
    logger.info("generating statistics for OWN-PT")
    statistics = Statistics(ownpt)
    
    polysemy_pt = statistics.get_polysemy("OWN-PT")
    base_pt, core_pt = statistics.get_base_core("OWN-PT")
    instantiated_synsets_pt = statistics.get_defined("OWN-PT")
    multi_word_expressions_pt = statistics.get_multi_word_expressions("OWN-PT")
    synsets_pt, senses_pt, words_pt = statistics.get_synsets_senses_words("OWN-PT")
    ## en
    logger.info("generating statistics for OWN-EN")
    statistics = Statistics(ownen)

    polysemy_en = statistics.get_polysemy("OWN-EN")
    base_en, core_en = statistics.get_base_core("OWN-EN")
    instantiated_synsets_en = statistics.get_defined("OWN-EN")
    multi_word_expressions_en = statistics.get_multi_word_expressions("OWN-EN")
    synsets_en, senses_en, words_en = statistics.get_synsets_senses_words("OWN-EN")

    # serializes output
    logger.info(f"serializing output to '{output_filepath}'")

    with open(output_filepath, "w") as outfile:
        outfile.write("#+title: Statistics")

        # Summary
        outfile.write("\n\n* Summary\n")
        outfile.write(tabulate.tabulate(
            tablefmt="orgtbl",
            headers=["Wordnet","Lang","Words","Senses"],
            tabular_data=[
                ["OWN-PT", "pt", words_pt, senses_pt],
                ["OWN-EN", "en", words_en, senses_en]]))
        
        # BaseConcept and CoreConcept
        outfile.write("\n\n* Base and Core Concepts\n")
        outfile.write(tabulate.tabulate(
            tablefmt="orgtbl",
            headers=["Synset Type","OWN-PT","OWN-EN"],
            tabular_data=[
                ["CoreConcept", f"{core_pt} ({round(100*core_pt/core_en, 2)}%)", f"{core_en} ({round(100*core_en/core_en, 2)}%)"],
                ["BaseComcept", f"{base_pt} ({round(100*base_pt/base_en, 2)}%)", f"{base_en} ({round(100*base_en/base_en, 2)}%)"]]))

        # Instantiated Synsets
        outfile.write("\n\n* Instantiated Synsets\n")
        table_pt = instantiated_synsets_pt
        table_en = instantiated_synsets_en
        outfile.write(tabulate.tabulate(
            tablefmt="orgtbl",
            headers=["Synset Type","OWN-PT","OWN-EN"],
            tabular_data=[[key, table_pt[key], table_en[key]] for key in table_pt]))
                
        # Multi Word Expressions
        outfile.write("\n\n* Multi Word Expressions\n")
        table_pt = multi_word_expressions_pt
        table_en = multi_word_expressions_en
        outfile.write(tabulate.tabulate(
            tablefmt="orgtbl",
            headers=["Synset Type","OWN-PT","OWN-EN"],
            tabular_data=[[key, table_pt[key], table_en[key]] for key in table_pt]))
        
        # Polysemy
        outfile.write("\n\n* Polysemy (1 Word / + Words)\n")
        table_pt = polysemy_pt
        table_en = polysemy_en
        outfile.write(tabulate.tabulate(
            tablefmt="orgtbl",
            headers=["Synset Type","OWN-PT","OWN-EN"],
            tabular_data=[[
                key, 
                f"{table_pt[key][0]} / {table_pt[key][1]}",
                f"{table_en[key][0]} / {table_en[key][1]}"]for key in table_pt]))

        outfile.write("\n")

# sets parser and interface function
parser = argparse.ArgumentParser()

# sets the user options
parser.add_argument("--ownpt", help="files from ownpt", nargs="+")
parser.add_argument("--ownen", help="files from ownen", nargs="+")
parser.add_argument("-o", help="output (default: statistics.org)", default="statistics.org")

parser.add_argument("-v", help="increase verbosity (example: -vv for debugging)", action="count", default=0)

# cals the parser
_parse(parser.parse_args())