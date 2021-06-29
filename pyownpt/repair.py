# -*- coding: utf-8 -*-

from rdflib.graph import Graph
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
            self.remove_desconex_word_nodes, # without a sense
            
            self.fix_links_to_satelites,
            self.fix_synset_id_types,
            self.remove_lemma_property]

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


    def add_morpho_exceptions(self, exceptions):
        """"""

        self.logger.info(f"start processing {len(exceptions)} exceptions")
        # add exceptions
        for form, *lemmas in exceptions:
            for lemma in lemmas:
                self.logger.debug(f"processing exception: {form} {lemma}")
            
                word = self._get_word(lemma)
                if word is not None:
                    form = self._new_lexical_literal(form)
                    self._add_triple((word, SCHEMA.exceptionalForm, form), "add_exceptions")
                else:
                    self.logger.warning(f"could not process exception: {form} {lemma}")
            
        # print statistics
        self.logger.info(f"after action, {self.added_triples} triples were added")


    def add_adjective_markers(self, senses:Graph, adjective_lines):
        """"""
        
        self.logger.info(f"start processing {len(adjective_lines)} lines")

        # format data
        adjective_data = []
        for line in adjective_lines:
            synset_id, _, _, words_count, *tail = line.split()
            for i in range(int(words_count, base=16)):
                adjective_data.append((synset_id, tail[2*i]))
        
        # find and add adjective markers
        count = 0
        for synset_id, word in adjective_data:
            marker = None
            if word.endswith("(a)"): marker = "a" # predicate position
            elif word.endswith("(p)"): marker = "p" # prenominal (attributive) position
            elif word.endswith("(ip)"): marker = "ip" # immediately postnominal position
            else:
                continue
            
            # adds marker
            valid = False
            word = self._format_lexical(word[:word.find(f"({marker})")], True)
            for synset in self.graph.subjects(SCHEMA.synsetId, Literal(synset_id)):
                sense = self._get_sense(synset, word)
                if sense is not None:
                    valid = True
                    count += 1
                    self.logger.debug(f"adding marker '{marker}' from word '{word}' to sense '{sense.n3()}'")
                    senses.add((sense, SCHEMA.adjPosition, Literal(marker)))
            # validates the result
            if not valid:    
                self.logger.warning(f"could not add marker '{marker}' from word '{word}' to synset '{synset_id}'")

        # print statistics
        self.logger.info(f"after action {count} triples were added")


    def remove_lemma_property(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?p ?o WHERE { VALUES ?p { wn30:lemma } ?s ?p ?o . }"
        result = self.graph.query(query)

        for triple in result:
            count += 1
            self._drop_triple(triple)

        # how many actions
        return count


    def fix_synset_id_types(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE { VALUES ?t { wn30:Synset wn30:AdjectiveSatelliteSynset wn30:AdjectiveSynset wn30:AdverbSynset wn30:NounSynset wn30:VerbSynset } ?s a ?t . }"
        result = self.graph.query(query)

        for synset, in result:
            synset_id = synset.split("/synset-")[-1].split("-")[0]
            new_synset_id = Literal(synset_id)
            old_synset_id = self.graph.value(synset, SCHEMA.synsetId)
            if not old_synset_id == new_synset_id:
                count += 1
                if old_synset_id is not None:
                    self._drop_triple((synset, SCHEMA.synsetId, old_synset_id), name)
                self._add_triple((synset, SCHEMA.synsetId, new_synset_id), name)

        # how many actions
        return count


    def fix_links_to_satelites(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s2 WHERE { VALUES ?p { wn30:adverbPertainsTo wn30:derivationallyRelated wn30:classifiesByUsage wn30:classifiesByTopic wn30:classifiesByRegion } ?s1 ?p ?s2 . ?s1 a wn30:WordSense . FILTER NOT EXISTS { ?s2 a ?t . } }"
        result = self.graph.query(query)

        for sense, in result:
            new_sense = URIRef(sense.replace("-a-", "-s-"))
            if sense == new_sense:
                continue
            if ((new_sense, RDF.type, SCHEMA.WordSense)) in self.graph:
                count += 1
                self._replace_node(sense, new_sense, name)
            else:
                self.logger.warning(f"sense {sense.n3()} not replaced by {new_sense.n3()}: undefined new sense")

        # how many actions
        return count

        
    def replace_word_uris(self, name=""):
        """"""
        count = 0

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

        query = "SELECT ?s ?p ?o WHERE{ VALUES ?p { rdfs:label wn30:lexicalForm wn30:gloss wn30:example wn30:lemma } ?s ?p ?o . }"
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
