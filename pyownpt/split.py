# -*- coding: utf-8 -*-

from rdflib.graph import Graph
from pyownpt.ownpt import OWNPT

class Split(OWNPT):

    def get_splitted(self):
        """"""

        splitted = dict()
        name_action_map = [
            ("morphosemantic-links",self.get_morphosemantic_links),
            ("same-as",self.get_same_as),
            ("relations",self.get_relations),
            ("words",self.get_words),
            ("wordsenses",self.get_wordsenses),
            ("synsets",self.get_base_synsets)]

        for name, action in name_action_map:
            self.logger.info(f"generating graph for {name}")
            
            splitted[name] = action()
            for triple in splitted[name]:
                self._drop_triple(triple)

        return splitted


    def get_morphosemantic_links(self):
        # cat own-pt-morpho.nt | grep "https://w3id.org/own-pt/nomlex" > own-files/own-pt-morphosemantic-links.nt
        query = "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX(STR(?s), 'https://w3id.org/own-pt/nomlex') || REGEX(STR(?p), 'https://w3id.org/own-pt/nomlex') || REGEX(STR(?o), 'https://w3id.org/own-pt/nomlex')) }"
        return self._get_graph(query)


    def get_same_as(self):
        # cat own-pt-morpho.nt | grep "https://w3id.org/own-pt/nomlex" -v | grep "sameAs" > own-files/own-pt-same-as.nt
        query = "SELECT ?s ?p ?o WHERE{ VALUES ?p { owl:sameAs } ?s ?p ?o . }"
        return self._get_graph(query)


    def get_relations(self):
        # cat own-pt-morpho.nt | grep "https://w3id.org/own-pt/nomlex" -v | grep "sameAs" -v | egrep "(https://w3id.org/own-pt/wn30/schema/adjectivePertainsTo|https://w3id.org/own-pt/wn30/schema/adverbPertainsTo|https://w3id.org/own-pt/wn30/schema/antonymOf|https://w3id.org/own-pt/wn30/schema/attribute|https://w3id.org/own-pt/wn30/schema/causes|https://w3id.org/own-pt/wn30/schema/classifiedByRegion|https://w3id.org/own-pt/wn30/schema/classifiedByTopic|https://w3id.org/own-pt/wn30/schema/classifiedByUsage|https://w3id.org/own-pt/wn30/schema/classifiesByRegion|https://w3id.org/own-pt/wn30/schema/classifiesByTopic|https://w3id.org/own-pt/wn30/schema/classifiesByUsage|https://w3id.org/own-pt/wn30/schema/derivationallyRelated|https://w3id.org/own-pt/wn30/schema/entails|https://w3id.org/own-pt/wn30/schema/hasInstance|https://w3id.org/own-pt/wn30/schema/hypernymOf|https://w3id.org/own-pt/wn30/schema/hyponymOf|https://w3id.org/own-pt/wn30/schema/instanceOf|https://w3id.org/own-pt/wn30/schema/similarTo|https://w3id.org/own-pt/wn30/schema/substanceHolonymOf|https://w3id.org/own-pt/wn30/schema/substanceMeronymOf|https://w3id.org/own-pt/wn30/schema/memberHolonymOf|https://w3id.org/own-pt/wn30/schema/memberMeronymOf|https://w3id.org/own-pt/wn30/schema/partHolonymOf|https://w3id.org/own-pt/wn30/schema/participleOf|https://w3id.org/own-pt/wn30/schema/partMeronymOf|https://w3id.org/own-pt/wn30/schema/sameVerbGroupAs|https://w3id.org/own-pt/wn30/schema/seeAlso)" > own-files/own-pt-relations.nt
        query = "SELECT ?s ?p ?o WHERE{ VALUES ?p { wn30:adjectivePertainsTo wn30:adverbPertainsTo wn30:antonymOf wn30:attribute wn30:causes wn30:classifiedByRegion wn30:classifiedByTopic wn30:classifiedByUsage wn30:classifiesByRegion wn30:classifiesByTopic wn30:classifiesByUsage wn30:derivationallyRelated wn30:entails wn30:hasInstance wn30:hypernymOf wn30:hyponymOf wn30:instanceOf wn30:similarTo wn30:substanceHolonymOf wn30:substanceMeronymOf wn30:memberHolonymOf wn30:memberMeronymOf wn30:partHolonymOf wn30:participleOf wn30:partMeronymOf wn30:sameVerbGroupAs wn30:seeAlso } ?s ?p ?o . }"
        return self._get_graph(query)


    def get_words(self):
        # cat own-pt-morpho.nt | grep "https://w3id.org/own-pt/nomlex" -v | grep "sameAs" -v | egrep "(https://w3id.org/own-pt/wn30/schema/adjectivePertainsTo|https://w3id.org/own-pt/wn30/schema/adverbPertainsTo|https://w3id.org/own-pt/wn30/schema/antonymOf|https://w3id.org/own-pt/wn30/schema/attribute|https://w3id.org/own-pt/wn30/schema/causes|https://w3id.org/own-pt/wn30/schema/classifiedByRegion|https://w3id.org/own-pt/wn30/schema/classifiedByTopic|https://w3id.org/own-pt/wn30/schema/classifiedByUsage|https://w3id.org/own-pt/wn30/schema/classifiesByRegion|https://w3id.org/own-pt/wn30/schema/classifiesByTopic|https://w3id.org/own-pt/wn30/schema/classifiesByUsage|https://w3id.org/own-pt/wn30/schema/derivationallyRelated|https://w3id.org/own-pt/wn30/schema/entails|https://w3id.org/own-pt/wn30/schema/hasInstance|https://w3id.org/own-pt/wn30/schema/hypernymOf|https://w3id.org/own-pt/wn30/schema/hyponymOf|https://w3id.org/own-pt/wn30/schema/instanceOf|https://w3id.org/own-pt/wn30/schema/similarTo|https://w3id.org/own-pt/wn30/schema/substanceHolonymOf|https://w3id.org/own-pt/wn30/schema/substanceMeronymOf|https://w3id.org/own-pt/wn30/schema/memberHolonymOf|https://w3id.org/own-pt/wn30/schema/memberMeronymOf|https://w3id.org/own-pt/wn30/schema/partHolonymOf|https://w3id.org/own-pt/wn30/schema/participleOf|https://w3id.org/own-pt/wn30/schema/partMeronymOf|https://w3id.org/own-pt/wn30/schema/sameVerbGroupAs|https://w3id.org/own-pt/wn30/schema/seeAlso)" -v | egrep "/word-" > own-files/own-pt-words.nt
        query = "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX(STR(?s), '/word-') || REGEX(STR(?p), '/word-') || REGEX(STR(?o), '/word-')) }"
        return self._get_graph(query)


    def get_wordsenses(self):
        # cat own-pt-morpho.nt | grep "https://w3id.org/own-pt/nomlex" -v | grep "sameAs" -v | egrep "(https://w3id.org/own-pt/wn30/schema/adjectivePertainsTo|https://w3id.org/own-pt/wn30/schema/adverbPertainsTo|https://w3id.org/own-pt/wn30/schema/antonymOf|https://w3id.org/own-pt/wn30/schema/attribute|https://w3id.org/own-pt/wn30/schema/causes|https://w3id.org/own-pt/wn30/schema/classifiedByRegion|https://w3id.org/own-pt/wn30/schema/classifiedByTopic|https://w3id.org/own-pt/wn30/schema/classifiedByUsage|https://w3id.org/own-pt/wn30/schema/classifiesByRegion|https://w3id.org/own-pt/wn30/schema/classifiesByTopic|https://w3id.org/own-pt/wn30/schema/classifiesByUsage|https://w3id.org/own-pt/wn30/schema/derivationallyRelated|https://w3id.org/own-pt/wn30/schema/entails|https://w3id.org/own-pt/wn30/schema/hasInstance|https://w3id.org/own-pt/wn30/schema/hypernymOf|https://w3id.org/own-pt/wn30/schema/hyponymOf|https://w3id.org/own-pt/wn30/schema/instanceOf|https://w3id.org/own-pt/wn30/schema/similarTo|https://w3id.org/own-pt/wn30/schema/substanceHolonymOf|https://w3id.org/own-pt/wn30/schema/substanceMeronymOf|https://w3id.org/own-pt/wn30/schema/memberHolonymOf|https://w3id.org/own-pt/wn30/schema/memberMeronymOf|https://w3id.org/own-pt/wn30/schema/partHolonymOf|https://w3id.org/own-pt/wn30/schema/participleOf|https://w3id.org/own-pt/wn30/schema/partMeronymOf|https://w3id.org/own-pt/wn30/schema/sameVerbGroupAs|https://w3id.org/own-pt/wn30/schema/seeAlso)" -v | egrep "/word-" -v | egrep "/wordsense-" > own-files/own-pt-wordsenses.nt
        query = "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX(STR(?s), '/wordsense-') || REGEX(STR(?p), '/wordsense-') || REGEX(STR(?o), '/wordsense-')) }"
        return self._get_graph(query)


    def get_base_synsets(self):
        # cat own-pt-morpho.nt | grep "https://w3id.org/own-pt/nomlex" -v | grep "sameAs" -v | egrep "(https://w3id.org/own-pt/wn30/schema/adjectivePertainsTo|https://w3id.org/own-pt/wn30/schema/adverbPertainsTo|https://w3id.org/own-pt/wn30/schema/antonymOf|https://w3id.org/own-pt/wn30/schema/attribute|https://w3id.org/own-pt/wn30/schema/causes|https://w3id.org/own-pt/wn30/schema/classifiedByRegion|https://w3id.org/own-pt/wn30/schema/classifiedByTopic|https://w3id.org/own-pt/wn30/schema/classifiedByUsage|https://w3id.org/own-pt/wn30/schema/classifiesByRegion|https://w3id.org/own-pt/wn30/schema/classifiesByTopic|https://w3id.org/own-pt/wn30/schema/classifiesByUsage|https://w3id.org/own-pt/wn30/schema/derivationallyRelated|https://w3id.org/own-pt/wn30/schema/entails|https://w3id.org/own-pt/wn30/schema/hasInstance|https://w3id.org/own-pt/wn30/schema/hypernymOf|https://w3id.org/own-pt/wn30/schema/hyponymOf|https://w3id.org/own-pt/wn30/schema/instanceOf|https://w3id.org/own-pt/wn30/schema/similarTo|https://w3id.org/own-pt/wn30/schema/substanceHolonymOf|https://w3id.org/own-pt/wn30/schema/substanceMeronymOf|https://w3id.org/own-pt/wn30/schema/memberHolonymOf|https://w3id.org/own-pt/wn30/schema/memberMeronymOf|https://w3id.org/own-pt/wn30/schema/partHolonymOf|https://w3id.org/own-pt/wn30/schema/participleOf|https://w3id.org/own-pt/wn30/schema/partMeronymOf|https://w3id.org/own-pt/wn30/schema/sameVerbGroupAs|https://w3id.org/own-pt/wn30/schema/seeAlso)" -v | egrep "/word-" -v | egrep "/wordsense-" -v > own-files/own-pt-synsets.nt
        query = "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX(STR(?s), '/synset-') || REGEX(STR(?p), '/synset-') || REGEX(STR(?o), '/synset-') || REGEX(STR(?s), STR(skos:)) || REGEX(STR(?p), STR(skos:)) || REGEX(STR(?o), STR(skos:)) || REGEX(STR(?s), STR(dc:)) || REGEX(STR(?p), STR(dc:)) || REGEX(STR(?o), STR(dc:)) ) }"
        return self._get_graph(query)


    def _get_graph(self, query):

        graph = OWNPT(Graph(), None)
        for triple in self.graph.query(query):
            graph._add_triple(triple)
        
        return graph.graph
