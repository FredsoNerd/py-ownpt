# -*- coding: utf-8 -*-

from rdflib.graph import Graph
from pyown.own import OWN

class Split(OWN):

    def pop_morphosemantic_links(self):
        queries = [
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?s), '/nomlex-')) }",
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?o), '/nomlex-')) }",
            "SELECT ?s ?p ?o WHERE{ VALUES ?p { owns:agent owns:bodyPart owns:byMeansOf owns:destination owns:event owns:instrument owns:location owns:material owns:property owns:result owns:state owns:undergoer owns:uses owns:vehicle } ?s ?p ?o . }"
        ]
        return self._split_graph(queries)

    def pop_same_as(self):
        queries = [
            "SELECT ?s ?p ?o WHERE{ VALUES ?p { owl:sameAs } ?s ?p ?o . }"
        ]
        return self._split_graph(queries)

    def pop_relations(self):
        queries = [
            "SELECT ?s ?p ?o WHERE{ VALUES ?p { owns:adjectivePertainsTo owns:adverbPertainsTo owns:antonymOf owns:attribute owns:causes owns:classifiedByRegion owns:classifiedByTopic owns:classifiedByUsage owns:classifiesByRegion owns:classifiesByTopic owns:classifiesByUsage owns:derivationallyRelated owns:entails owns:hasInstance owns:hypernymOf owns:hyponymOf owns:instanceOf owns:similarTo owns:substanceHolonymOf owns:substanceMeronymOf owns:memberHolonymOf owns:memberMeronymOf owns:partHolonymOf owns:participleOf owns:partMeronymOf owns:sameVerbGroupAs owns:seeAlso } ?s ?p ?o . }"
        ]
        return self._split_graph(queries)

    def pop_words(self):
        queries = [
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?s), '/word-')) }",
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?o), '/word-')) }"
        ]
        return self._split_graph(queries)

    def pop_wordsenses(self):
        queries = [
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?s), '/wordsense-')) }",
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?o), '/wordsense-')) }"
        ]
        return self._split_graph(queries)

    def pop_base_synsets(self):
        queries = [
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?s), '/synset-')) }",
            "SELECT ?s ?p ?o WHERE{ ?s ?p ?o . FILTER( REGEX( STR(?o), '/synset-')) }",
            "SELECT ?s ?p ?o WHERE{ VALUES ?o { skos:ConceptScheme } ?s ?p ?o . }",
            "SELECT ?s ?p ?o WHERE{ VALUES ?p { dc:title } ?s ?p ?o . }"
        ]
        return self._split_graph(queries)

    def _split_graph(self, queries:list):
        graph = OWN(Graph(), None)
        # populate for each query
        for query in queries:
            # draw each from query
            for triple in self.graph.query(query):
                graph._add_triple(triple)
                self.graph.remove(triple)
        return graph.graph