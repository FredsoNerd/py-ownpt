# -*- coding: utf-8 -*-

import logging
from re import T
from typing import AbstractSet
from urllib.parse import scheme_chars
import tqdm

from pyownpt.ownpt import OWNPT, RDFS, SYNSETPT, SCHEMA


class Update(OWNPT):

    def update(
        self,
        doc_suggestions = [],
        doc_votes = [],
        users_senior=[],
        trashold_senior=1,
        trashold_junior=2):
        """"""

        votes = [x["_source"] for x in doc_votes]
        suggestions = [x["_source"] for x in doc_suggestions]
        
        self.logger.info("formatting suggestions to apply")
        
        # filter suggestions
        suggestions = self._filter_suggestions(
                        suggestions, votes, users_senior,
                        trashold_senior, trashold_junior)                
        # sort results
        suggestions = sorted(suggestions, key=lambda x:x["action"], reverse=True)
        suggestions = sorted(suggestions, key=lambda x:x["date"])


        # apply suggestions
        self.logger.info("start applying suggestions")
        self._apply_suggestions(suggestions)

        # statistics
        self.logger.info(f"total triples added by action: {self.added_triples}")
        self.logger.info(f"total triples removed by action: {self.removed_triples}")


    def update_from_compare(self, report):
        """"""

        # formats
        self.logger.info("formatting suggestions to apply")
        suggestions = []
        for doc_id, doc_report in report.items():
            for action, params in doc_report["actions"].items():
                for param in params:
                    suggestions.append({"doc_id":doc_id,"params":param,"action":action})
        
        # sort results
        suggestions = sorted(suggestions, key=lambda x:x["action"], reverse=True)

        # apply suggestions
        self.logger.info("start applying suggestions")
        self._apply_suggestions(suggestions)


    def _apply_suggestions(self, suggestions:list):
        """"""
        
        for suggestion in tqdm.tqdm(suggestions):
            self._apply_suggestion(suggestion)


    def _apply_suggestion(self, suggestion):
        action = suggestion["action"]
        params = suggestion["params"]
        doc_id = suggestion["doc_id"]
        synset = self._get_synset_by_id(doc_id)
        pos = self._get_pos(synset, "synset-")

        result = True

        if action == "add-word-pt":
            # checks and adds suitable
            item = self._get_sense(synset, params)
            if item is not None:
                result = False
            else:
                word = self._get_word(params, True, pos)
                sense = self._new_sense(synset, True)
                label = self._new_lexical_literal(params)
                self._add_triple((sense, RDFS.label, label), action)
                self._add_triple((sense, SCHEMA.word, word), action)
            
        elif action == "add-gloss-pt":
            # checks and adds suitable
            item = self._get_gloss(synset, params)
            if item is not None:
                result = False
            else:
                item = self._new_lexical_literal(params, True)
                self._add_triple((synset, SCHEMA.gloss, item), action)

        elif action == "add-example-pt":
            # checks and adds suitable
            item = self._get_example(synset, params)
            if item is not None:
                result = False
            else:
                item = self._new_lexical_literal(params, True)
                self._add_triple((synset, SCHEMA.example, item), action)

        elif action == "remove-word-pt":
            # finds and removes suitable
            item = self._get_sense(synset, params)
            if item is None:
                result = False
            else:
                self._drop_node(item, action)
                # removes word if it becomes orphan 
                word = self.graph.value(item, SCHEMA.word)
                sense = self.graph.value(predicate=SCHEMA.word, object=word)
                if sense is not None:
                    self._drop_node(word, action)
        
        elif action == "remove-gloss-pt":
            # finds and removes suitable
            item = self._get_gloss(synset, params)
            if item is None:
                result = False
            else:
                self._drop_triple((synset, SCHEMA.gloss, item), action)
            
        elif action == "remove-example-pt":
            # finds and removes suitable
            item = self._get_example(synset, params)
            if item is None:
                result = False
            else:
                self._drop_triple((synset, SCHEMA.example, item), action)
            
        else:
            self.logger.warning(f"invalid action: {action}")

        # resulting
        if result:
            term = "added to" if action.startswith("add") else "removed from"
            self.logger.debug(f"{action}: param '{params}' {term} '{synset.n3()}'")
        else:
            term = "already" if action.startswith("add") else "not"
            self.logger.debug(f"{action}: param '{params}' {term} in '{synset.n3()}'")


    def _filter_suggestions(
        self,
        suggestions:list,
        votes:list,
        users_senior:list,
        trashold_senior:int,
        trashold_junior:int):
        """"""

        # joins suggestions and votes
        f_idl = lambda x: x["id"]
        f_idr = lambda x: x["suggestion_id"]
        zipped = self._left_zip_by_id(suggestions, votes, f_idl, f_idr)

        # apply filter rules and return
        return [x[0] for x in zipped if self._rules(*x,users_senior,trashold_senior,trashold_junior)]


    def _rules(
        self,
        suggestion,
        votes:list,
        users_senior:list,
        trashold_senior:int,
        trashold_junior:int):
        """"""

        
        r1 = suggestion["status"] == "new"
        # r1 = suggestion["status"] == "committed"
        r2 = suggestion["action"] != "comment"
        score = sum([vote["value"] for vote in votes])
        r3 = score >= trashold_senior and suggestion["user"] in users_senior or score >= trashold_junior

        return all([r1,r2,r3])


    def _left_zip_by_id(self, listl, listr, f_idl, f_idr):
        """"""

        # review eficiency
        zipped = {f_idl(l):{"l":l,"r":[]} for l in listl}
        for itemr in listr:
            _id = f_idr(itemr)
            if _id in zipped:
                zipped[_id]["r"].append(itemr)
            else:
                self.logger.debug(f"invalid id: {_id}")
                # raise Exception(f"Got invalid id to zip: {_id}")

        return [(item["l"],item["r"]) for item in zipped.values()]
