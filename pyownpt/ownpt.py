# -*- coding: utf-8 -*-

import re
import logging

from rdflib import Graph, URIRef, Namespace, Literal, RDF, RDFS, OWL
from rdflib.plugins.sparql import prepareQuery

# global
PWN30 = Namespace("http://wordnet-rdf.princeton.edu/wn30/")

SCHEMA = Namespace("https://w3id.org/own-pt/wn30/schema/")
NOMLEX = Namespace("https://w3id.org/own-pt/nomlex/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSETPT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")

WORD_EN = Namespace("https://w3id.org/own-pt/wn30-en/instances/word-")
SYNSET_EN = Namespace("https://w3id.org/own-pt/wn30-en/instances/synset-")
WORDSENSE_EN = Namespace("https://w3id.org/own-pt/wn30-en/instances/wordsense-")


class OWNPT():
    def __init__(self, graph:Graph, lang="pt"):
        self.lang = lang
        self.graph = graph
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("wn30", SCHEMA)
        self.graph.bind("pwn30", PWN30)
        self.graph.bind("nomlex", NOMLEX)

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
            new_triple = (synset, SCHEMA.containsWordSense, new_sense)

            # validate new sense
            if new_triple not in self.graph:
                break
            
            # update counter
            sense_id += 1

        # connect sense
        if add_sense:
            self._add_triple((new_sense, RDF.type, SCHEMA.WordSense))
            self._add_triple((synset, SCHEMA.containsWordSense, new_sense))
            self._add_triple((new_sense, SCHEMA.wordNumber, Literal(str(sense_id))))

        return new_sense


    def _get_sense(self, synset, lexical:str):
        """"""

        lexical = self._format_lexical(lexical)
        for sense in self.graph.objects(synset, SCHEMA.containsWordSense):
            label = self.graph.value(sense, RDFS.label)
            label = self._format_lexical(label)
            if label == lexical:
                return sense
        
        return None


    def _word_uri_by_blank(self, sense, word):
        """"""

        # if word has lexical form
        lexical_form = self.graph.value(word, SCHEMA.lexicalForm)
        if lexical_form is not None:
            lexical_form = lexical_form.toPython()
            return self._new_word(lexical_form)

        # otherwise
        sense_label = self.graph.value(sense, RDFS.label)
        lexical = sense_label.toPython()
        return self._get_word(lexical, True)


    def _get_word(self, lexical_form:str, create_new=False):
        """"""

        lexical_form = Literal(lexical_form, lang=self.lang)
        word = self.graph.value(predicate=SCHEMA.lexicalForm, object=lexical_form)
        if word is None and create_new:
            return self._new_word(lexical_form, True)
        else:
            return word


    def _new_word(self, lexical:str, add_word=False):
        """"""

        word = re.sub(r" ", "+", lexical).strip()
        word = re.sub(r"\<", "_", word).strip()
        word = re.sub(r"\>", "_", word).strip()
        # word = re.sub(r"\-", "_", word).strip()
        # word = re.sub(r"\?", "_", word).strip()
        # word = re.sub(r"\!", "_", word).strip()
        # word = re.sub(r"\(", "_", word).strip()
        # word = re.sub(r"\)", "_", word).strip()
        # word = re.sub(r"(\<|\>|\?|\!|\(|\))", "_", word).strip()
        if self.lang == "pt": word = WORD[word]
        if self.lang == "en": word = WORD_EN[word]
        if add_word:
            self._add_triple((word, RDF.type, SCHEMA.Word))
            lexical_form = Literal(lexical, lang=self.lang)
            self._add_triple((word, SCHEMA.lexicalForm, lexical_form), "new_word")

        return word


    def _replace_node(self, old_node, new_node, prefix="replace"):
        """"""

        self.logger.debug(f"{prefix}:replacing node '{old_node.n3()}' by '{new_node.n3()}'")

        # replaces objects
        result = self.graph.subject_predicates(old_node)
        for s,p in result:
            self._drop_triple((s,p,old_node), prefix)
            self._add_triple((s,p,new_node), prefix)
        
        # replaces subjects
        result = self.graph.predicate_objects(old_node)
        for p, o in result:
            self._drop_triple((old_node,p,o), prefix)
            self._add_triple((new_node,p,o), prefix)


    def _drop_node(self, node, prefix="drop_node"):
        """"""
        
        self.logger.debug(f"{prefix}:dropping node '{node.n3()}'")

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
        return Literal(lexical, lang=self.lang)


    def _format_lexical(self, lexical, replace_punctuation=False):
        if replace_punctuation:
            lexical = re.sub(r"\_", " ", lexical).strip()
        return re.sub(r"\s+", " ", lexical).strip()


    def _get_gloss(self, synset, lexical_form:str):
        """"""
        
        lexical_form = self._format_lexical(lexical_form)
        for gloss in self.graph.objects(synset, SCHEMA.gloss):
            lexical = gloss.toPython()
            if self._format_lexical(lexical) == lexical_form:
                return gloss
        
        return None

    
    def _get_example(self, synset, lexical_form:str):
        """"""
        
        lexical_form = self._format_lexical(lexical_form)
        for example in self.graph.objects(synset, SCHEMA.example):
            lexical = example.toPython()
            if self._format_lexical(lexical) == lexical_form:
                return example
        
        return None


    def _get_node_id(self, sense):
        return self._get_node_suffix(sense)


    def _get_synset_id(self, synset):
        return self._get_node_suffix(synset)


    def _get_node_suffix(self, node):
        return f"{self.lexicon_id}-{node.split('instances/')[-1]}"

    
    def _get_pos(self, element, separator="wordsense-"):
        return element.split(separator)[-1].split("-")[1]

    
    def _get_all_words(self):
        return self.graph.query("SELECT ?w WHERE { ?w a wn30:Word }")
    
    
    def _get_all_synsets(self):
        return self.graph.query("SELECT ?s WHERE { VALUES ?t { wn30:Synset wn30:AdjectiveSatelliteSynset wn30:AdjectiveSynset wn30:AdverbSynset wn30:NounSynset wn30:VerbSynset } ?s a ?t . }")
        