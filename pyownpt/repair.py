# -*- coding: utf-8 -*-

from pyownpt.ownpt import OWNPT, Literal, RDFS, RDF, SCHEMA


class Repair(OWNPT):

    def repair(self):
        """"""

        # actions to apply
        repair_actions = [
            self.fix_sense_blank_nodes, 
            self.remove_blank_words, # words that are blank nodes
            self.remove_void_words, # without lexical form
            self.remove_double_words, # more than one lexical form
            self.expand_sense_words, # create word by label
            self.add_word_types, # grant well typed nodes
            self.add_sense_types, # grant well typed nodes
            self.add_sense_labels, # create labels by word
            self.add_sense_number, # add sense word number
            self.format_lexicals, # well defined lexical form
            self.replace_sense_labels, # match labels to words
            self.remove_word_duplicates, # with same lexical form
            self.remove_sense_duplicates, # same label in a synset
            self.remove_desconex_sense_nodes, # without a synset
            self.remove_desconex_word_nodes] # without a sense

        # apply actions 
        for action in repair_actions:
            # computes added/removed before action
            before_added_triples = self.added_triples
            before_removed_triples = self.removed_triples
            # run action
            action_cases = action()
            # computes added/removed after action
            after_added_triples = self.added_triples
            after_removed_triples = self.removed_triples
            
            # plots info
            name = action.__name__
            self.logger.info(
                f"action '{name}' applied to {action_cases} cases:"
                    f"\n\t{name}:{after_added_triples - before_added_triples} triples added"
                    f"\n\t{name}:{after_removed_triples - before_removed_triples} triples removed")

        # resulting added and removed triples
        self.logger.info(
            f"all {len(repair_actions)} actions applied"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def remove_desconex_word_nodes(self):
        """"""

        query = "SELECT ?w WHERE{ ?w rdf:type wn30:Word . FILTER NOT EXISTS { ?s ?p ?w . } } "
        result = self.graph.query(query)
        
        for word, in result:
            self._drop_node(word, "remove_desconex_word_nodes")

        # how many actions
        return len(result)


    def remove_desconex_sense_nodes(self):
        """"""

        query = "SELECT ?s WHERE{ { ?s wn30:word ?w . } UNION { ?s rdf:type wn30:WordSense . } FILTER NOT EXISTS { ?ss wn30:containsWordSense ?s . } } "
        result = self.graph.query(query)
        
        for sense, in result:
            self._drop_node(sense, "remove_desconex_sense_nodes")

        # how many actions
        return len(result)


    def remove_sense_duplicates(self):
        """"""

        query = "SELECT ?s1 ?s2 WHERE{ ?s1 rdfs:label ?l . ?ss wn30:containsWordSense ?s1 . ?s2 rdfs:label ?l . ?ss wn30:containsWordSense ?s2 . FILTER ( STR(?s1) < STR(?s2) ) }"
        result = self.graph.query(query)
        
        for word1, word2 in result:
            self._drop_node(word2, "remove_sense_duplicates")

        # how many actions
        return len(result)


    def remove_word_duplicates(self):
        """"""

        query = "SELECT ?w1 ?w2 WHERE{ ?w1 wn30:lexicalForm ?l . ?w2 wn30:lexicalForm ?l . FILTER ( STR(?w1) < STR(?w2) ) }"
        result = self.graph.query(query)
        for word1, word2 in result:
            self._replace_node(word2, word1, "remove_word_duplicates")

        # how many actions
        return len(result)


    def remove_double_words(self):
        """"""
        
        query = "SELECT ?w WHERE{ ?ss wn30:containsWordSense ?s . ?s wn30:word ?w . ?w wn30:lexicalForm ?l1 . ?w wn30:lexicalForm ?l2 . FILTER ( ?l1 != ?l2 ) }"
        result = self.graph.query(query)

        for word, in result:
            self._drop_node(word, "expand_double_words")

            # sense_label = self.graph.value(sense, HAS_LABEL)
            # if sense_label.toPython() == lexical.toPython():
            #     new_sense = sense
            #     word = self._get_word(lexical.toPython(), True)
            #     self._add_triple((new_sense, SCHEMA.word, word), "expand_double_words")

        # how many actions
        return len(result)


    def format_lexicals(self):
        """"""

        query = "SELECT ?s ?p ?o WHERE{ VALUES ?p { rdfs:label wn30:lexicalForm wn30:gloss wn30:example } ?s ?p ?o . FILTER ( lang(?o) != 'pt') }"
        result = self.graph.query(query)
        
        for s, p, lexical in result:
            self._drop_triple((s, p, lexical), "add_literal_tag_pt")
            lexical = self._new_lexical_literal(lexical.toPython())
            self._add_triple((s, p, lexical), "add_literal_tag_pt")

        # how many actions
        return len(result)


    def add_word_types(self):
        """"""

        query = "SELECT ?w WHERE{ ?s wn30:word ?w . FILTER NOT EXISTS { ?w rdf:type ?t .} }"
        result = self.graph.query(query)
        
        for word, in result:
            self._add_triple((word, RDF.type, SCHEMA.Word), "add_word_types")

        # how many actions
        return len(result)


    def add_sense_types(self):
        """"""

        query = "SELECT ?s WHERE{ { ?ss wn30:containsWordSense ?s . } FILTER NOT EXISTS { ?s rdf:type ?t .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            self._add_triple((sense, RDF.type, SCHEMA.WordSense), "add_sense_types")

        # how many actions
        return len(result)


    def replace_sense_labels(self):
        """"""

        query = "SELECT ?s ?sl ?wl WHERE{ ?s rdfs:label ?sl . ?s wn30:word ?w . ?w wn30:lexicalForm ?wl . FILTER ( ?sl != ?wl )}"
        result = self.graph.query(query)
        
        for sense, label, lexical in result:
            self._drop_triple((sense, RDFS.label, label), "replace_sense_labels")
            self._add_triple((sense, RDFS.label, lexical), "replace_sense_labels")

        # how many actions
        return len(result)

    def add_sense_number(self):
        """"""

        query = "SELECT ?s WHERE{ ?ss wn30:containsWordSense ?s . FILTER NOT EXISTS { ?s wn30:wordNumber ?n .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            word_number = sense.split("-")[-1]
            word_number = Literal(word_number)
            self._add_triple((sense, SCHEMA.wordNumber, word_number), "add_sense_number")

        # how many actions
        return len(result)



    def add_sense_labels(self):
        """"""

        query = "SELECT ?s WHERE{ ?ss wn30:containsWordSense ?s . FILTER NOT EXISTS { ?s rdfs:label ?l .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            word = self.graph.value(sense, SCHEMA.word)
            label = self.graph.value(word, SCHEMA.containsWordSense)
            label = self._new_lexical_literal(label.toPython(), False)
            self._add_triple((sense, RDFS.label, label), "add_sense_labels")

        # how many actions
        return len(result)


    def expand_sense_words(self):
        """"""

        query = "SELECT ?s ?l WHERE{ ?ss wn30:containsWordSense ?s . ?s rdfs:label ?l . FILTER NOT EXISTS { ?s wn30:word ?w . } }"
        result = self.graph.query(query)
        
        for sense, label in result:
            lexical = label.toPython()
            word = self._get_word(lexical, True)
            self._add_triple((sense, SCHEMA.word, word), "expand_sense_words")

        # how many actions
        return len(result)


    def remove_void_words(self):
        """"""
        
        query = "SELECT ?s ?w WHERE{ ?s wn30:word ?w . FILTER NOT EXISTS { ?w wn30:lexicalForm ?l .} }"
        result = self.graph.query(query)
        
        for sense, word in result:
            self._drop_triple((sense, SCHEMA.word, word), "remove_void_words")

        # how many actions
        return len(result)


    def remove_blank_words(self):
        """"""
        
        query = "SELECT ?s ?w WHERE { ?s wn30:word ?w . FILTER ( isBlank(?w) ) }"
        result = self.graph.query(query)

        for sense, word in result:
            self._drop_node(word, "remove_blank_words")
            # new_word = self._word_uri_by_blank(sense, word)
            # self._replace_node(word, new_word, "fix_word_blank_nodes")

        # how many actions
        return len(result)


    def fix_sense_blank_nodes(self):
        """"""
        
        query = "SELECT ?ss ?s WHERE { ?ss wn30:containsWordSense ?s . FILTER ( isBlank(?s) ) }"
        result = self.graph.query(query)

        for synset, sense in result:
            new_sense = self._new_sense(synset, False)
            self._replace_node(sense, new_sense, "fix_sense_blank_nodes")

        # how many actions
        return len(result)
