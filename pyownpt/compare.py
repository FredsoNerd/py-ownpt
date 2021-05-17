# -*- coding: utf-8 -*-

import tqdm
import logging

from rdflib import Graph, URIRef
from pyownpt.ownpt import SCHEMA, NOMLEX, SYNSETPT


class Compare():
    
    def __init__(self, graph:Graph, dump:dict):
        self.graph = graph
        self.dump = dump
        self.docs = {synset["doc_id"]:synset for synset in self.dump}

        # logging
        self.logger = logging.getLogger("compare")


    def compare_items(self):
        """"""

        # compares items
        _, report_word = self.compare_item_ownpt_dump(item_name="word_pt")
        _, report_gloss = self.compare_item_ownpt_dump(item_name="gloss_pt")
        _, report_example = self.compare_item_ownpt_dump(item_name="example_pt")
        report_word = report_word["docs"]
        report_gloss = report_gloss["docs"]
        report_example = report_example["docs"]

        # joins results
        report = dict()
        for doc_id in report_word:
            report[doc_id] = dict()

            report[doc_id]["compare"] = all({
                report_word[doc_id]["word_pt"]["compare"],
                report_gloss[doc_id]["gloss_pt"]["compare"],
                report_example[doc_id]["example_pt"]["compare"]
            })
            
            report[doc_id].update(report_word[doc_id])
            report[doc_id].update(report_gloss[doc_id])
            report[doc_id].update(report_example[doc_id])
        
        return report


    def compare_item_ownpt_dump(self, item_name="word_pt"):
        """"""

        # reports
        compare = True
        report = {
            "docs":dict(), 
            "count":{"dump":0, "ownpt":0, "both":0}}
        
        # query
        query = self._get_query(item_name)

        # start comparing
        self.logger.warning(f"start comparing item {item_name}:")
        for synset in tqdm.tqdm(self.dump):
            doc_id = synset['doc_id']

            result, items, itemsd, itemso = self._compare_item(synset, item_name, query)
            
            # update report
            report["count"]["both"] += len(items)
            report["count"]["dump"] += len(itemsd)
            report["count"]["ownpt"] += len(itemso)
            
            report["docs"][doc_id] = dict()
            report["docs"][doc_id][item_name] = {"compare":result, "both":items, "dump":itemsd, "ownpt":itemso}

            # displays debug info
            if not result:
                compare = False
                self.logger.debug(f"synset {doc_id}:words: comparing resulted False:"
                                f"\n\t {item_name} {itemsd} found only in dump"
                                f"\n\t {item_name} {itemso} found only in ownpt"
                                f"\n\t {item_name} {items} found in both documents")
        
        self.logger.info(f"{item_name}: comparing resulted '{compare}':"
                        f"\n\t {item_name}:{report['count']['dump']} found only in dump"
                        f"\n\t {item_name}:{report['count']['ownpt']} found only in ownpt"
                        f"\n\t {item_name}:{report['count']['both']} found in both documents")

        # returns report
        return compare, report


    def compare_antonymof_ownpt_dump(self):
        """"""

        map_pointers = {"wn30_pt_antonymOf":SCHEMA.antonymOf}
        return self._compare_pointers_ownpt_dump(map_pointers)

    
    def compare_morpho_ownpt_dump(self):
        """"""

        ownpt = Graph()

        # morphosemantic links
        pointers_uri_map = {  
            "wn30_pt_property": NOMLEX.property,
            "wn30_pt_result": NOMLEX.result,
            "wn30_pt_state": NOMLEX.state,
            "wn30_pt_undergoer": NOMLEX.undergoer,
            "wn30_pt_uses": NOMLEX.uses,
            "wn30_pt_vehicle": NOMLEX.vehicle,
            "wn30_pt_event": NOMLEX.event,
            "wn30_pt_instrument": NOMLEX.instrument,
            "wn30_pt_location": NOMLEX.location,
            "wn30_pt_material": NOMLEX.material,
            "wn30_pt_agent": NOMLEX.agent,
            "wn30_pt_bodyPart": NOMLEX.bodyPart,
            "wn30_pt_byMeansOf": NOMLEX.byMeansOf
        }

        return self._compare_pointers_ownpt_dump(pointers_uri_map)


    def _compare_pointers_ownpt_dump(self, map_pointers:dict):
        """"""

        compare = True
        reports = dict()

        for pointer_name, pointer_uri in map_pointers.items():
            compare_i, reports[pointer_name] = self._compare_pointer_ownpt_dump(pointer_name, pointer_uri)
            compare = compare if compare_i else False
        
        return compare, reports


    def _compare_pointer_ownpt_dump(self, pointer_name, pointer_uri):
        """"""

        # reports
        compare = True
        report = {
            "count":{"dump":0, "ownpt":0, "both":0},
            "pairs":{"dump":[], "ownpt":[], "both":[]}}

        self.logger.warning(f"start comparing pointer '{pointer_name}':")
        for synset in tqdm.tqdm(self.dump):
            doc_id = synset['doc_id']

            result, pairs, pairsd, pairso = self._compare_pointers(synset, pointer_name, pointer_uri)

            # update report
            report["count"]["both"] += len(pairs)
            report["count"]["dump"] += len(pairsd)
            report["count"]["ownpt"] += len(pairso)
            report["pairs"]["both"] += pairs
            report["pairs"]["dump"] += pairsd
            report["pairs"]["ownpt"] += pairso
            
            # display debug
            if not result:
                compare = False
                self.logger.debug(f"synset {doc_id}:{pointer_name}: comparing resulted False:"
                                f"\n\t pairs {pairsd} found only in dump"
                                f"\n\t pairs {pairso} found only in ownpt"
                                f"\n\t pairs {pairs} found in both documents")
        
        self.logger.info(f"{pointer_name}: comparing resulted '{compare}':"
                        f"\n\t {report['count']['dump']} pairs found only in dump"
                        f"\n\t {report['count']['ownpt']} pairs found only in ownpt"
                        f"\n\t {report['count']['both']} pairs found in both documents")

        # returns report
        return compare, report


    def _compare_item(self, synset:dict, item_name:str, query:str):
        """"""  
        compare = True
        
        # report words
        items = []
        itemso = []
        itemsd = synset[item_name].copy() if item_name in synset else []
        itemsd = [item.strip() for item in itemsd]

        # finds all wordsenses, and its words
        doc_id = synset["doc_id"]
        synset_uri = SYNSETPT[doc_id]
        
        result = self.graph.query(query.format(
                    synset = synset_uri.n3(),
                    hassens = SCHEMA.containsWordSense.n3(),
                    hasword = SCHEMA.word.n3(),
                    lexical = SCHEMA.lexicalForm.n3(),
                    hasgloss = SCHEMA.gloss.n3(),
                    hasexample = SCHEMA.example.n3()))
        
        # compares words in synset with dump
        for item, in result:
            item = item.toPython().strip()

            # checks if word exists in dump
            if item in itemsd:
                items.append(item)
                itemsd.remove(item)
            else:
                itemso.append(item)

        # check if unique words are void
        if len(itemsd) > 0: compare = False
        if len(itemso) > 0: compare = False
        
        return compare, items, itemsd, itemso


    def _compare_pointers(self, synset:dict, pointer_name:str, pointer_uri:URIRef):
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
                source = self._get_source_target(synset, pointer, "source_word")
                
                # target senses/synset
                target_synset = self.docs[pointer["target_synset"]]
                target = self._get_source_target(target_synset, pointer, "target_word")
                
                # pairs
                if source and target:
                    pairsd.append((source, target))

        # finds pointers
        doc_id = synset["doc_id"]
        synset_uri = SYNSETPT[doc_id]
        
        query = ("SELECT ?ss ?sw ?swl ?ts ?tw ?twl WHERE{{"
                    "?ss {pointer} ?ts ."
                    "{synset} {hassens} ?ss ."
                    "?ss {hasword} ?sw . ?sw {lexical} ?swl ."
                    "?ts {hasword} ?tw . ?tw {lexical} ?twl . }}")
        result = self.graph.query(query.format(
                    synset = synset_uri.n3(),
                    hassens = SCHEMA.containsWordSense.n3(),
                    pointer = pointer_uri.n3(),
                    hasword = SCHEMA.word.n3(),
                    lexical = SCHEMA.lexicalForm.n3()))
        

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


    def _get_source_target(self, synset, pointer, key):
        """"""
        
        word = pointer[key] if key in pointer else None
        words = synset["word_pt"] if "word_pt" in synset else []

        if word is None:
            return synset
        if word in words:
            return word
        
        return None


    def _get_query(self, item_name):
        """"""

        if item_name == "word_pt":
            return "SELECT ?wl WHERE {{ {synset} {hassens} ?s . ?s {hasword} ?w . ?w {lexical} ?wl . }}"
        if item_name == "gloss_pt":
            return "SELECT ?gl WHERE {{ {synset} {hasgloss} ?gl . }}"
        if item_name == "example_pt":
            return "SELECT ?ex WHERE {{ {synset} {hasexample} ?ex . }}"
        
        raise Exception(f"not a valid option for comparing: {item_name}")

