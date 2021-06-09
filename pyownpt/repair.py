# -*- coding: utf-8 -*-

from pyownpt.ownpt import OWNPT, Literal, URIRef, RDFS, RDF, SCHEMA

class Repair(OWNPT):

    def repair(self):
        """"""

        # actions to apply
        repair_actions = [
            self.add_word_types,
            self.remove_blank_words, # words that are blank nodes
            self.remove_void_words, # without lexical form
            self.remove_double_words, # more than one lexical form

            self.add_sense_types,
            self.replace_blank_senses, # senses that are blank nodes
            self.expand_sense_words, # create word by label
            self.add_sense_labels, # create labels by word
            self.add_sense_number, # add sense word number

            self.format_lexicals, # well defined lexical form
            self.replace_word_uris, # grant unique words uri
            
            self.replace_sense_labels, # match labels to words
            self.remove_word_duplicates, # with same lexical form
            self.remove_sense_duplicates, # same label in a synset
            self.remove_desconex_sense_nodes, # without a synset
            self.remove_desconex_word_nodes,
            
            self.fix_links_to_satelites] # without a sense

        # apply actions 
        for action in repair_actions:
            name = action.__name__
            
            # computes added/removed before action
            before_added_triples = self.added_triples
            before_removed_triples = self.removed_triples
            # run action
            action_cases = action(name)
            # computes added/removed after action
            after_added_triples = self.added_triples
            after_removed_triples = self.removed_triples
            
            # plots info
            self.logger.info(
                f"action '{name}' applied to {action_cases} cases:"
                    f"\n\t{name}:{after_added_triples - before_added_triples} triples added"
                    f"\n\t{name}:{after_removed_triples - before_removed_triples} triples removed")

        # resulting added and removed triples
        self.logger.info(
            f"all {len(repair_actions)} actions applied"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def fix_links_to_satelites(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s2 WHERE { VALUES ?p { wn30:adverbPertainsTo wn30:derivationallyRelated wn30:classifiesByUsage wn30:classifiesByTopic wn30:classifiesByRegion } ?s1 ?p ?s2 . FILTER NOT EXISTS { ?s2 a ?t . } }"
        result = self.graph.query(query)

        for sense, in result:
            new_sense = URIRef(sense.replace("-a-", "-s-"))
            if ((new_sense, RDF.type, SCHEMA.WordSense)) in self.graph:
                count += 1
                self._replace_node(sense, new_sense, name)

        # how many actions
        return count

        
    def replace_word_uris(self, name=""):
        """"""
        count = 0
        
        # not necessary if english
        if self.lang == "en" or self.lang is None: return 0

        query = "SELECT ?w ?l WHERE { ?w rdf:type wn30:Word . ?w wn30:lexicalForm ?l }"
        result = self.graph.query(query)
        
        for word, lexical in result:
            new_word = self._new_word(lexical, True)
            if not new_word == word:
                count += 1
                self._replace_node(word, new_word, name)

        # how many actions
        return count


    def remove_desconex_word_nodes(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w WHERE{ ?w rdf:type wn30:Word . FILTER NOT EXISTS { ?s ?p ?w . } } "
        result = self.graph.query(query)
        
        for word, in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def remove_desconex_sense_nodes(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE{ ?s rdf:type wn30:WordSense . FILTER NOT EXISTS { ?ss wn30:containsWordSense ?s . } } "
        result = self.graph.query(query)
        
        for sense, in result:
            count += 1
            self._drop_node(sense, name)

        # how many actions
        return count


    def remove_sense_duplicates(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s2 WHERE{ ?ss wn30:containsWordSense ?s1; wn30:containsWordSense ?s2 . ?s1 rdfs:label ?l . ?s2 rdfs:label ?l . FILTER ( STR(?s1) < STR(?s2) ) }"
        result = self.graph.query(query)
        
        for sense2, in result:
            count += 1
            self._drop_node(sense2, name)

        # how many actions
        return count


    def remove_word_duplicates(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w1 ?w2 WHERE{ ?w1 wn30:lexicalForm ?l . ?w2 wn30:lexicalForm ?l . FILTER ( STR(?w1) < STR(?w2) ) }"
        result = self.graph.query(query)
        for word1, word2 in result:
            count += 1
            self._replace_node(word2, word1, name)

        # how many actions
        return count


    def remove_double_words(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?w WHERE{ ?w wn30:lexicalForm ?l1 . ?w wn30:lexicalForm ?l2 . FILTER ( ?l1 != ?l2 ) }"
        result = self.graph.query(query)

        for word, in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def format_lexicals(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?p ?o WHERE{ VALUES ?p { rdfs:label wn30:lexicalForm wn30:gloss wn30:example } ?s ?p ?o . }"
        result = self.graph.query(query)
        
        for s, p, lexical in result:
            new_lexical = self._format_lexical(lexical.toPython(), True)
            new_lexical = self._new_lexical_literal(new_lexical, True)
            if not new_lexical == lexical:
                count += 1
                self._drop_triple((s, p, lexical), name)
                self._add_triple((s, p, new_lexical), name)

        # how many actions
        return count


    def add_word_types(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w WHERE{ { ?s wn30:word ?w } UNION { ?w wn30:lexicalForm ?l } . FILTER NOT EXISTS { ?w rdf:type ?t .} }"
        result = self.graph.query(query)
        
        for word, in result:
            count += 1
            self._add_triple((word, RDF.type, SCHEMA.Word), name)

        # how many actions
        return count


    def add_sense_types(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE{ { ?ss wn30:containsWordSense ?s . } UNION { ?s wn30:word ?w } FILTER NOT EXISTS { ?s rdf:type ?t .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            count += 1
            self._add_triple((sense, RDF.type, SCHEMA.WordSense), name)

        # how many actions
        return count


    def replace_sense_labels(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?sl ?wl WHERE{ ?s rdfs:label ?sl . ?s wn30:word ?w . ?w wn30:lexicalForm ?wl . FILTER ( ?sl != ?wl )}"
        result = self.graph.query(query)
        
        for sense, label, lexical in result:
            count += 1
            self._drop_triple((sense, RDFS.label, label), name)
            self._add_triple((sense, RDFS.label, lexical), name)

        # how many actions
        return count

    def add_sense_number(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE{ ?ss wn30:containsWordSense ?s . FILTER NOT EXISTS { ?s wn30:wordNumber ?n .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            count += 1
            word_number = sense.split("-")[-1]
            word_number = Literal(word_number)
            self._add_triple((sense, SCHEMA.wordNumber, word_number), name)

        # how many actions
        return count



    def add_sense_labels(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?l WHERE{ ?s rdf:type wn30:WordSense . ?s wn30:word ?w . ?w wn30:lexicalForm ?l . FILTER NOT EXISTS { ?s rdfs:label ?l .} }"
        result = self.graph.query(query)
        
        for sense, label in result:
            count += 1
            label = self._new_lexical_literal(label.toPython(), False)
            self._add_triple((sense, RDFS.label, label), name)

        # how many actions
        return count


    def expand_sense_words(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?l WHERE{ ?s rdf:type wn30:WordSense . ?s rdfs:label ?l . FILTER NOT EXISTS { ?s wn30:word ?w . } }"
        result = self.graph.query(query)
        
        for sense, label in result:
            count += 1
            lexical = label.toPython()
            word = self._get_word(lexical, True)
            self._add_triple((sense, SCHEMA.word, word), name)

        # how many actions
        return count


    def remove_void_words(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?w WHERE{ ?w rdf:type wn30:Word . FILTER NOT EXISTS { ?w wn30:lexicalForm ?l .} }"
        result = self.graph.query(query)
        
        for word in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def remove_blank_words(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?w WHERE { ?w rdf:type wn30:Word . FILTER ( isBlank(?w) ) }"
        result = self.graph.query(query)

        for word, in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def replace_blank_senses(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?ss ?s WHERE { ?ss wn30:containsWordSense ?s . FILTER ( isBlank(?s) ) }"
        result = self.graph.query(query)

        for synset, sense in result:
            count += 1
            new_sense = self._new_sense(synset, False)
            self._replace_node(sense, new_sense, name)

        # how many actions
        return count
