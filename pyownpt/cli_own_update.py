# -*- coding: utf-8 -*-

from json import loads
from rdflib import Graph
from pyownpt.update import update_ownpt_from_dump

def cli_update_ownpt_from_dump(
    ownpt_filapath:str,
    wn_filepath:str,
    ownpt_format:str="nt",
    output_filepath:str="output.xml",
    output_format:str="xml"):
    """"""

    doc_wn = [loads(line) for line in open(wn_filepath).readlines()]
    wn = [item["_source"] for item in doc_wn]

    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)
    update_ownpt_from_dump(ownpt, wn)

    # saves results
    ownpt.serialize(output_filepath, format=output_format, encoding="utf8")

cli_update_ownpt_from_dump(
    "/home/fredson/openWordnet-PT/unzipped/own-pt.nt",
    "/home/fredson/openWordnet-PT/dump/outfile.json",
    "nt",
    "/home/fredson/openWordnet-PT/unzipped/output.nt",
    "nt")