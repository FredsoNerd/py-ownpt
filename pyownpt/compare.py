# -*- coding: utf-8 -*-

import tqdm
import logging
logger = logging.getLogger(__name__)

from rdflib import Graph, Namespace, URIRef, BNode
from rdflib import Literal, XSD, RDF, RDFS, SKOS, OWL

# global
OWNPT = Namespace("https://w3id.org/own-pt/wn30/schema/")
SYNSET_PT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")


def compare_ownpt_dump(ownpt:Graph, wn:dict):
    """"""
    report = dict()
    report["words"] = dict()
    compare_words, report_words = compare_words_ownpt_dump(ownpt, wn)

    map_pointers = {"wn30_pt_antonymOf":OWNPT.antonymOf}
    compare_anto, report_anto = compare_pointers_ownpt_dump(ownpt, wn, map_pointers)

    return compare_words, report_words, compare_anto, report_anto

def compare_words_ownpt_dump(ownpt:Graph, wn:dict):
    """"""

    # reports
    compare = True
    report = {"count":{"dump":0, "ownpt":0, "both":0}}
    
    logger.warning(f"start comparing words:")
    for synset in tqdm.tqdm(wn):
        doc_id = synset['doc_id']

        result, words, wordsd, wordso = _compare_words(ownpt, synset)
        
        # update report
        report["count"]["both"] += len(words)
        report["count"]["dump"] += len(wordsd)
        report["count"]["ownpt"] += len(wordso)
        report[doc_id] = {"compare":result, "both":words, "dump":wordsd, "ownpt":wordso}

        # displays debug info
        if not result:
            compare = False
            logger.debug(f"synset {doc_id}:words: comparing resulted False:"
                            f"\n\t words {wordsd} found only in dump"
                            f"\n\t words {wordso} found only in ownpt"
                            f"\n\t words {words} found in both documents")
    
    logger.info(f"words: comparing resulted '{compare}':"
                    f"\n\t {report['count']['dump']} words found only in dump"
                    f"\n\t {report['count']['ownpt']} words found only in ownpt"
                    f"\n\t {report['count']['both']} words found in both documents")

    # returns report
    return compare, report


def compare_pointers_ownpt_dump(ownpt:Graph, wn:dict, map_pointers:dict):
    """"""

    compare = True
    reports = dict()
    map_docs = {synset["doc_id"]:synset for synset in wn}

    for pointer_name, pointer_uri in map_pointers.items():
        compare_i, reports[pointer_name] = _compare_pointers_ownpt_dump(ownpt, wn, pointer_name, pointer_uri, map_docs)
        compare = compare if compare_i else False
    
    return compare, reports


def _compare_pointers_ownpt_dump(ownpt:Graph, wn:dict, pointer_name, pointer_uri, map_docs):
    """"""

    # reports
    compare = True
    report = {
        "count":{"dump":0, "ownpt":0, "both":0},
        "pairs":{"dump":[], "ownpt":[], "both":[]}}

    logger.warning(f"start comparing pointer '{pointer_name}':")
    for synset in tqdm.tqdm(wn):
        doc_id = synset['doc_id']

        result_antonym, pairs, pairsd, pairso = _compare_pointers(ownpt, synset, map_docs, pointer_name, pointer_uri)

        # update report
        report["count"]["both"] += len(pairs)
        report["count"]["dump"] += len(pairsd)
        report["count"]["ownpt"] += len(pairso)
        report["pairs"]["both"] += pairs
        report["pairs"]["dump"] += pairsd
        report["pairs"]["ownpt"] += pairso
        
        # display debug
        if not result_antonym:
            compare = False
            logger.debug(f"synset {doc_id}:{pointer_name}: comparing resulted False:"
                            f"\n\t pairs {pairsd} found only in dump"
                            f"\n\t pairs {pairso} found only in ownpt"
                            f"\n\t pairs {pairs} found in both documents")
    
    logger.info(f"{pointer_name}: comparing resulted '{compare}':"
                    f"\n\t {report['count']['dump']} pairs found only in dump"
                    f"\n\t {report['count']['ownpt']} pairs found only in ownpt"
                    f"\n\t {report['count']['both']} pairs found in both documents")

    # returns report
    return compare, report


def _compare_words(ownpt:Graph, synset:dict):
    """"""  
    compare = True
    
    # report words
    words = []
    wordso = []
    wordsd = synset["word_pt"].copy() if "word_pt" in synset else []

    # finds all wordsenses, and its words
    doc_id = synset["doc_id"]
    synset_uri = SYNSET_PT[doc_id]
    
    query = ("SELECT ?s ?w ?wl WHERE{{ "
                "{synset} {hassens} ?s ."
                "?s {hasword} ?w ."
                "?w {lexical} ?wl . }}")
    result = ownpt.query(query.format(
                synset = synset_uri.n3(),
                hassens = OWNPT.containsWordSense.n3(),
                hasword = OWNPT.word.n3(),
                lexical = OWNPT.lexicalForm.n3()))
    
    # compares words in synset with dump
    for _, _, wordl in result:
        wordl = wordl.toPython().strip()

        # checks if word exists in dump
        if wordl in wordsd:
            words.append(wordl)
            wordsd.remove(wordl)
        else:
            wordso.append(wordl)

    # check if unique words are void
    if len(wordsd) > 0: compare = False
    if len(wordso) > 0: compare = False
    
    return compare, words, wordsd, wordso


def _compare_pointers(ownpt:Graph, synset:dict, map_doc:dict, pointer_name:str, pointer_uri:URIRef):
    """"""
    compare = True
    
    # pointers
    pairs = []
    pairso = []
    pairsd = []

    # find pairs with source in this synset
    if pointer_name in synset:
        for pointer in synset[pointer_name]:
            # source senses/synset
            source = _get_source_target(synset, pointer, "source_word")
            # target senses/synset
            target_synset = map_doc[pointer["target_synset"]]
            target = _get_source_target(target_synset, pointer, "target_word")
            # pairs
            pairsd.append((source, target))

    # finds pointers
    doc_id = synset["doc_id"]
    synset_uri = SYNSET_PT[doc_id]
    
    query = ("SELECT ?ss ?sw ?swl ?ts ?tw ?twl WHERE{{"
                "?ss {pointer} ?ts ."
                "{synset} {hassens} ?ss ."
                "?ss {hasword} ?sw . ?sw {lexical} ?swl ."
                "?ts {hasword} ?tw . ?tw {lexical} ?twl . }}")
    result = ownpt.query(query.format(
                synset = synset_uri.n3(),
                hassens = OWNPT.containsWordSense.n3(),
                pointer = pointer_uri.n3(),
                hasword = OWNPT.word.n3(),
                lexical = OWNPT.lexicalForm.n3()))
    

    # compares words in synset with dump
    for _, _, source_word, _, _, target_word in result:
        source_word = source_word.toPython().strip()
        target_word = target_word.toPython().strip()
        pair = (source_word, target_word)

        # checks if pair exists in dump
        if pair in pairsd:
            pairs.append(pair)
            pairsd.remove(pair)
        else:
            pairso.append(pair)

    # check if unique words are void
    if len(pairsd) > 0: compare = False
    if len(pairso) > 0: compare = False
    
    return compare, pairs, pairsd, pairso


def _get_source_target(synset, pointer, key):
    """"""
    
    word = pointer[key] if key in pointer else None
    words = synset["word_pt"] if "word_pt" in synset else []

    if word is None: return synset
    if word in words: return word
    
    return None