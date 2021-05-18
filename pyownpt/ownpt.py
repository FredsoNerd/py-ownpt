# -*- coding: utf-8 -*-

import re
import logging

from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib import XSD, RDF, RDFS, SKOS, OWL

# global
SCHEMA = Namespace("https://w3id.org/own-pt/wn30/schema/")
NOMLEX = Namespace("https://w3id.org/own-pt/nomlex/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSETPT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")

HAS_TYPE = RDF.type
HAS_LABEL = RDFS.label

TYPE_WORD = SCHEMA.Word
TYPE_WORDSENSE = SCHEMA.WordSense

NOMLEX_NOUN = NOMLEX.noun
NOMLEX_VERB = NOMLEX.verb

CONTAINS_WORD = SCHEMA.word
CONTAINS_GLOSS = SCHEMA.gloss
CONTAINS_EXAMPLE = SCHEMA.example
CONTAINS_WORDSENSE = SCHEMA.containsWordSense
CONTAINS_WORD_NUMBER = SCHEMA.wordNumber
CONTAINS_LEXICAL_FORM = SCHEMA.lexicalForm


class OWNPT():
    def __init__(self, graph:Graph):
        self.graph = graph

        # statistics
        self.added_triples = 0
        self.removed_triples = 0

        # logging
        self.logger = logging.getLogger("ownpt")


    def _new_sense(self, synset, add_sense=False):
        """"""
        # synset_id from uri
        synset_id = synset.split("/")[-1]
        synset_id = synset_id[synset_id.find("-")+1:]
            
        # finds new sense_id 
        sense_id = 1
        while True:
            # new sense to add
            new_sense = WORDSENSE[f"{synset_id}-{sense_id}"]
            new_triple = (synset, CONTAINS_WORDSENSE, new_sense)

            # validate new sense
            if new_triple not in self.graph:
                break
            
            # update counter
            sense_id += 1

        # connect sense
        if add_sense:
            self._add_triple((new_sense, HAS_TYPE, TYPE_WORDSENSE))
            self._add_triple((synset, CONTAINS_WORDSENSE, new_sense))
            self._add_triple((new_sense, CONTAINS_WORD_NUMBER, Literal(str(sense_id))))

        return new_sense


    def _get_sense(self, synset, lexical:str):
        """"""

        lexical = self._format_lexical(lexical)
        for sense in self.graph.objects(synset, CONTAINS_WORDSENSE):
            label = self.graph.value(sense, HAS_LABEL)
            label = self._format_lexical(label)
            if label == lexical:
                return sense
        
        return None


    def _word_uri_by_blank(self, sense, word):
        """"""

        # if word has lexical form
        lexical_form = self.graph.value(word, CONTAINS_LEXICAL_FORM)
        if lexical_form is not None:
            lexical_form = lexical_form.toPython()
            return self._new_word(lexical_form)

        # otherwise
        sense_label = self.graph.value(sense, HAS_LABEL)
        lexical = sense_label.toPython()
        return self._get_word(lexical, True)


    def _get_word(self, lexical_form:str, create_new=False):
        """"""

        lexical_form = Literal(lexical_form, lang="pt")
        word =  self.graph.value(predicate=CONTAINS_LEXICAL_FORM, object=lexical_form)
        if word is None and create_new:
            return self._new_word(lexical_form, True)
        else:
            return word


    def _new_word(self, lexical_form:str, add_lexical=False):
        """"""

        word = WORD[lexical_form.replace(" ", "+")]
        # word = WORD[lexical_form.replace(" ", "_")]
        if add_lexical:
            self._add_triple((word, HAS_TYPE, TYPE_WORD))
            lexical_form = Literal(lexical_form, lang="pt")
            self._add_triple((word, CONTAINS_LEXICAL_FORM, lexical_form), "new_word")
            # self.graph.add((word, CONTAINS_LEXICAL_FORM, lexical_form))

        return word


    # def _word_by_sense(self, sense, add_lexical=False):
    #     """"""

    #     # if sense has lexical form on label
    #     sense_label = self.graph.value(sense, HAS_LABEL)
    #     if sense_label is not None:
    #         sense_label = sense_label.toPython()
    #         return self._get_word(sense_label, True)
        
    #     # otherwise
    #     return None


    def _replace_node(self, old_node, new_node, prefix="replace"):
        """"""

        self.logger.debug(f"{prefix}:replacing node '{old_node.n3()}' by '{new_node.n3()}'")

        # replaces objects
        result = self.graph.subject_predicates(old_node)
        for s,p in result:
            self._drop_triple((s,p,old_node), prefix)
            self._add_triple((s,p,new_node), prefix)
            # self.graph.add((s,p,new_node))
            # self.graph.remove((s,p,old_node))
        
        # replaces subjects
        result = self.graph.predicate_objects(old_node)
        for p, o in result:
            self._drop_triple((old_node,p,o), prefix)
            self._add_triple((new_node,p,o), prefix)
            # self.graph.add((new_node,p,o))
            # self.graph.remove((old_node,p,o))


    def _drop_node(self, node, prefix="drop_node"):
        """"""
        
        self.logger.debug(f"{prefix}:dropping node '{node.n3()}'")

        # self.graph.remove((node,None,None))
        # self.graph.remove((None,None,node))
        for triple in self.graph.triples((node,None,None)):
            self._drop_triple(triple, prefix)
        for triple in self.graph.triples((None,None,node)):
            self._drop_triple(triple, prefix)


    def _add_triple(self, triple, prefix="add_triple"):
        s,p,o = triple
        
        if triple not in self.graph:
            self.logger.debug(f"{prefix}:adding triple: {s.n3()} {p.n3()} {o.n3()}")
            self.graph.add(triple)

            # count triples added
            self.added_triples += 1

            return True
        
        # if not adding
        self.logger.debug(f"{prefix}:triple already in graph: {s.n3()} {p.n3()} {o.n3()}")
        return False

        
    def _drop_triple(self, triple, prefix="drop_triple"):
        s,p,o = triple

        if triple in self.graph:
            self.logger.debug(f"{prefix}:removing triple: {s.n3()} {p.n3()} {o.n3()}")
            self.graph.remove(triple)
            # count triples removed
            self.removed_triples += 1
            return True
        
        # if not removing
        self.logger.debug(f"{prefix}:triple not in graph: {s.n3()} {p.n3()} {o.n3()}")
        return False

    
    def _new_lexical_literal(self, lexical, format=False):
        if format:
            lexical = self._format_lexical(lexical)
        return Literal(lexical, lang="pt")


    def _format_lexical(self, lexical):
        return re.sub(r"\s+", " ", lexical).strip()


    def _get_gloss(self, synset, lexical_form:str):
        """"""
        
        lexical_form = self._format_lexical(lexical_form)
        for gloss in self.graph.objects(synset, CONTAINS_GLOSS):
            lexical = gloss.toPython()
            if self._format_lexical(lexical) == lexical_form:
                return gloss
        
        return None

    
    def _get_example(self, synset, lexical_form:str):
        """"""
        
        lexical_form = self._format_lexical(lexical_form)
        for example in self.graph.objects(synset, CONTAINS_EXAMPLE):
            lexical = example.toPython()
            if self._format_lexical(lexical) == lexical_form:
                return example
        
        return None