# -*- coding: utf-8 -*-

from logging import FATAL
from sys import flags
from pyownpt.ownpt import CONTAINS_EXAMPLE, CONTAINS_GLOSS, OWNPT
from pyownpt.ownpt import HAS_TYPE, HAS_LABEL
from pyownpt.ownpt import TYPE_WORD, TYPE_WORDSENSE
from pyownpt.ownpt import NOMLEX_NOUN, NOMLEX_VERB
from pyownpt.ownpt import CONTAINS_WORD, CONTAINS_WORDSENSE, CONTAINS_LEXICAL_FORM
from pyownpt.ownpt import CONTAINS_GLOSS, CONTAINS_EXAMPLE


class Repair(OWNPT):

    def repair(self):
        """"""

        # actions to apply
        repair_actions = [
            self.fix_word_blank_nodes,
            self.fix_sense_blank_nodes,
            self.remove_void_words, # without lexical form
            self.expand_double_words, # more than one lexical form
            self.expand_sense_words, # create word by label
            self.add_word_types, # grant well typed nodes
            self.add_sense_types, # grant well typed nodes
            self.add_sense_labels, # create labels by word
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

        query = "SELECT ?w WHERE{{ {{ ?w {haslexical} ?l . }} UNION {{ ?w {hastype} {typeword} . }} FILTER NOT EXISTS {{ {{ ?s {hasword} ?w . }} UNION  {{ ?s {nomlexnoum} ?w . }} UNION {{ ?s {nomlexverb} ?w . }} }} }} "
        result = self.graph.query(query.format(hastype = HAS_TYPE.n3(), hasword = CONTAINS_WORD.n3(), typeword = TYPE_WORD.n3(), haslexical = CONTAINS_LEXICAL_FORM.n3(), nomlexnoum = NOMLEX_NOUN.n3(), nomlexverb = NOMLEX_VERB.n3()))
        
        for word, in result:
            self._drop_node(word, "remove_desconex_word_nodes")

        # how many actions
        return len(result)


    def remove_desconex_sense_nodes(self):
        """"""

        query = "SELECT ?s WHERE{{ {{ ?s {hasword} ?w . }} UNION {{ ?s {hastype} {typesense} . }} FILTER NOT EXISTS {{ {{ ?ss {hassense} ?s . }} }} }} "
        result = self.graph.query(query.format(hastype = HAS_TYPE.n3(), hasword = CONTAINS_WORD.n3(), hassense = CONTAINS_WORDSENSE.n3(), typesense = TYPE_WORDSENSE.n3()))
        
        for sense, in result:
            self._drop_node(sense, "remove_desconex_sense_nodes")

        # how many actions
        return len(result)


    def remove_sense_duplicates(self):
        """"""

        query = "SELECT ?s1 ?s2 WHERE{{ ?s1 {haslabel} ?l . ?ss {hassense} ?s1 . ?s2 {haslabel} ?l . ?ss {hassense} ?s2 . FILTER ( STR(?s1) < STR(?s2) ) }}"
        result = self.graph.query(query.format(haslabel = HAS_LABEL.n3(), hassense = CONTAINS_WORDSENSE.n3()))
        
        for word1, word2 in result:
            self._replace_node(word2, word1, "remove_sense_duplicates")

        # how many actions
        return len(result)


    def remove_word_duplicates(self):
        """"""

        query = "SELECT ?w1 ?w2 WHERE{{ ?w1 {lexical} ?l . ?w2 {lexical} ?l . FILTER (?w1 != ?w2) }}"
        result = self.graph.query(query.format(lexical = CONTAINS_LEXICAL_FORM.n3()))
        
        for word1, word2 in result:
            self._replace_node(word2, word1, "remove_word_duplicates")

        # how many actions
        return len(result)


    # def expand_duple_senses(self):
    #     """"""

    #     query = "SELECT ?ss ?s ?w1 ?w2 WHERE{{ ?s {hasword} ?w1 . ?s {hasword} ?w2 . ?ss {hassense} ?s . FILTER ( ?w1 != ?w2 ) }}"
    #     result = self.graph.query(query.format(hasword = CONTAINS_WORD.n3(), hassense = CONTAINS_WORDSENSE.n3()))
        
    #     for synset, sense1, word1, word2 in result: 
    #         sense2 = self._new_sense(synset)
    #         self._drop_triple((sense1, CONTAINS_WORD, word2), "expand_duple_senses")
    #         self._add_triple((sense2, CONTAINS_WORD, word2), "expand_duple_senses")
    #         self._add_triple((synset, CONTAINS_WORDSENSE, sense2), "expand_duple_senses")

    #     # how many actions
    #     return len(result)


    def expand_double_words(self):
        """"""

        query = "SELECT?s ?w ?l1 WHERE{{ ?ss {hassense} ?s . ?s {hasword} ?w . ?w {haslexical} ?l1 . ?w {haslexical} ?l2 . FILTER ( ?l1 != ?l2 ) }}"
        result = self.graph.query(query.format(hassense = CONTAINS_WORDSENSE.n3(), hasword = CONTAINS_WORD.n3(), haslexical = CONTAINS_LEXICAL_FORM.n3()))
        
        for sense, word, lexical in result:
            self._drop_node(word, "expand_double_words")

            sense_label = self.graph.value(sense, HAS_LABEL)
            if sense_label.toPython() == lexical.toPython():
                new_sense = sense
                word = self._get_word(lexical.toPython(), True)
                self._add_triple((new_sense, CONTAINS_WORD, word), "expand_double_words")


        # how many actions
        return len(result)


    def format_lexicals(self):
        """"""

        query = "SELECT ?s ?p ?o WHERE{{ ?s ?p ?o . FILTER ( ?p = {haslabel} || ?p = {haslexical} || ?p = {hasgloss} || ?p = {hasexample} ) FILTER ( lang(?o) != 'pt') }}"
        result = self.graph.query(query.format(haslabel = HAS_LABEL.n3(), haslexical = CONTAINS_LEXICAL_FORM.n3(), hasgloss = CONTAINS_GLOSS.n3(), hasexample = CONTAINS_EXAMPLE.n3()))
        
        for s, p, lexical in result:
            self._drop_triple((s, p, lexical), "add_literal_tag_pt")
            lexical = self._new_lexical_literal(lexical.toPython())
            self._add_triple((s,p, lexical), "add_literal_tag_pt")

        # how many actions
        return len(result)


    def add_word_types(self):
        """"""

        query = "SELECT ?w WHERE{{ ?s {hasword} ?w . FILTER NOT EXISTS {{ ?w {hastype} ?t .}} }}"
        result = self.graph.query(query.format(hastype = HAS_TYPE.n3(), hasword = CONTAINS_WORD.n3()))
        
        for word, in result:
            self._add_triple((word, HAS_TYPE, TYPE_WORD), "add_word_types")

        # how many actions
        return len(result)


    def add_sense_types(self):
        """"""

        query = "SELECT ?s WHERE{{ {{ ?ss {hassense} ?s . }} FILTER NOT EXISTS {{ ?s {hastype} ?t .}} }}"
        result = self.graph.query(query.format(hastype = HAS_TYPE.n3(), hassense = CONTAINS_WORDSENSE.n3()))
        
        for sense, in result:
            self._add_triple((sense, HAS_TYPE, TYPE_WORDSENSE), "add_sense_types")

        # how many actions
        return len(result)


    def replace_sense_labels(self):
        """"""

        query = "SELECT ?s ?sl ?wl WHERE{{ ?s {haslabel} ?sl . ?s {hasword} ?w . ?w {haslexical} ?wl . FILTER (?sl != ?wl)}}"
        result = self.graph.query(query.format(haslabel = HAS_LABEL.n3(), hasword = CONTAINS_WORD.n3(), haslexical = CONTAINS_LEXICAL_FORM.n3()))
        
        for sense, label, lexical in result:
            self._drop_triple((sense, HAS_LABEL, label), "fix_sense_labels")
            self._add_triple((sense, HAS_LABEL, lexical), "fix_sense_labels")

        # how many actions
        return len(result)


    def add_sense_labels(self):
        """"""

        query = "SELECT ?s WHERE{{ ?ss {hassense} ?s . FILTER NOT EXISTS {{ ?s {haslabel} ?l .}} }}"
        result = self.graph.query(query.format(haslabel = HAS_LABEL.n3(), hassense = CONTAINS_WORDSENSE.n3()))
        
        for sense, in result:
            word = self.graph.value(sense, CONTAINS_WORD)
            label = self.graph.value(word, CONTAINS_LEXICAL_FORM)
            label = self._new_lexical_literal(label.toPython())
            self._add_triple((sense, HAS_LABEL, label), "add_sense_labels")

        # how many actions
        return len(result)


    def expand_sense_words(self):
        """"""

        query = "SELECT ?s ?l WHERE{{ ?ss {hassense} ?s . ?s {haslabel} ?l . FILTER NOT EXISTS {{ ?s {hasword} ?w . }} }}"
        result = self.graph.query(query.format(hasword = CONTAINS_WORD.n3(), haslabel = HAS_LABEL.n3(), hassense = CONTAINS_WORDSENSE.n3()))
        
        for sense, label in result:
            lexical = label.toPython()
            word = self._get_word(lexical, True)
            self._add_triple((sense, CONTAINS_WORD, word), "expand_sense_words")

        # how many actions
        return len(result)


    def remove_void_words(self):
        """"""
        
        query = ("SELECT ?s ?w WHERE{{ ?s {hasword} ?w . FILTER NOT EXISTS {{ ?w {lexical} ?wl .}} }}")
        result = self.graph.query(query.format(hasword = CONTAINS_WORD.n3(), lexical = CONTAINS_LEXICAL_FORM.n3()))
        
        for sense, word in result:
            self._drop_triple((sense, CONTAINS_WORD, word), "remove_void_words")

        # how many actions
        return len(result)


    def fix_word_blank_nodes(self):
        """"""
        
        query = "SELECT ?s ?o WHERE {{ ?s {predicate} ?o . FILTER ( isBlank(?o) ) }}"
        result = self.graph.query(query.format(predicate = CONTAINS_WORD.n3()))

        for sense, word in result:
            new_word = self._word_uri_by_blank(sense, word)
            self._replace_node(word, new_word, "fix_word_blank_nodes")

        # how many actions
        return len(result)


    def fix_sense_blank_nodes(self):
        """"""
        
        query = "SELECT ?s ?o WHERE {{ ?s {predicate} ?o . FILTER ( isBlank(?o) ) }}"
        result = self.graph.query(query.format(predicate = CONTAINS_WORDSENSE.n3()))

        for synset, sense in result:
            new_sense = self._new_sense(synset, False)
            self._replace_node(sense, new_sense, "fix_sense_blank_nodes")

        # how many actions
        return len(result)
