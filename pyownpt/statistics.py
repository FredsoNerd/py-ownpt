# -*- coding: utf-8 -*-

from os import stat
from rdflib.graph import Graph
from rdflib.namespace import OWL
from pyownpt.ownpt import NOMLEX, OWNPT, Literal, URIRef, RDFS, RDF, SCHEMA

class Statistics(OWNPT):


    def get_base_core(self, prefix="statistics"):
        # Base and Core
        self.logger.debug(f"getting statistics for types CoreConcept and BaseConcept")
        
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a wn30:CoreConcept ; wn30:containsWordSense ?s . }"
        own_core = self.graph.query(query).bindings[0]["count"].toPython()
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a wn30:BaseConcept ; wn30:containsWordSense ?s . }"
        own_base = self.graph.query(query).bindings[0]["count"].toPython()

        return own_base, own_core


    def get_defined(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Instantiated Synsets")

        # non void senses
        statistics = dict()
        for ss_type in ["NounSynset", "VerbSynset", "AdverbSynset", "AdjectiveSynset", "AdjectiveSatelliteSynset"]:
            # non void senses
            query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a wn30:"+ss_type+"; wn30:containsWordSense ?s . }"
            statistics[ss_type] = self.graph.query(query).bindings[0]["count"].toPython()

        # global
        ss_type = "Synset (total)"
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss wn30:containsWordSense ?s . }"
        statistics[ss_type] = self.graph.query(query).bindings[0]["count"].toPython()

        return statistics


    def get_polysemy(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Polysemy")
        
        # non void senses
        statistics = dict()
        for ss_type in ["NounSynset", "VerbSynset", "AdverbSynset", "AdjectiveSynset", "AdjectiveSatelliteSynset"]:
            # polysemy
            query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a wn30:"+ss_type+" ; wn30:containsWordSense ?s1 ; wn30:containsWordSense ?s2 . FILTER( ?s1 != ?s2 ) }"
            count_gt_1 = self.graph.query(query).bindings[0]["count"].toPython()
            query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss a wn30:"+ss_type+" ; wn30:containsWordSense ?s1 . FILTER NOT EXISTS { ?ss wn30:containsWordSense ?s2 . FILTER( ?s1 != ?s2 )}}"
            count_eq_1 = self.graph.query(query).bindings[0]["count"].toPython()

            statistics[ss_type] = count_eq_1, count_gt_1            

        # global
        ss_type = "Synset (total)"
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss wn30:containsWordSense ?s1 ; wn30:containsWordSense ?s2 . FILTER( ?s1 != ?s2 ) }"
        count_gt_1 = self.graph.query(query).bindings[0]["count"].toPython()
        query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss wn30:containsWordSense ?s1 . FILTER NOT EXISTS { ?ss wn30:containsWordSense ?s2 . FILTER( ?s1 != ?s2 )}}"
        count_eq_1 = self.graph.query(query).bindings[0]["count"].toPython()

        statistics[ss_type] = count_eq_1, count_gt_1

        # results
        return statistics


    def get_multi_word_expressions(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Multi Word Expressions")

        # non void senses
        statistics = dict()
        for pos in {"Noun":"n", "Verb":"v", "Adverb":"r", "Adjective":"a"}:
            # multi word expressions
            query = "SELECT (COUNT (DISTINCT ?w) as ?count) WHERE { ?w wn30:pos \""+pos+"\"; wn30:lemma ?l . FILTER REGEX( STR( ?l ), ' ') }"
            statistics[pos] = self.graph.query(query).bindings[0]["count"].toPython()

        # global
        pos = "Words (total)"
        query = "SELECT (COUNT ( DISTINCT ?w ) as ?count) WHERE { ?w wn30:lemma ?l . FILTER REGEX( STR( ?l ), ' ') }"
        statistics[pos] = self.graph.query(query).bindings[0]["count"].toPython()
        
        return statistics
    

    def get_summary(self, prefix="statistics"):
        """"""
        self.logger.debug(f"{prefix}:getting statistics for Summary")

        # synsets words and senses
        #query = "SELECT (COUNT( DISTINCT ?ss ) AS ?count) WHERE { ?ss wn30:containsWordSense ?s . }"
        #synsets = self.graph.query(query).bindings[0]["count"]
        query = "SELECT (COUNT( DISTINCT ?s ) AS ?count) WHERE { ?s a wn30:WordSense . }"
        senses = self.graph.query(query).bindings[0]["count"]
        query = "SELECT (COUNT( DISTINCT ?w ) AS ?count) WHERE { ?w a wn30:Word . }"
        words = self.graph.query(query).bindings[0]["count"]
        
        return senses, words
