# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from rdflib import Graph, Namespace, Literal, RDFS, RDF

# global
OWNPT = Namespace("https://w3id.org/own-pt/wn30/schema/")
NOMELEX = Namespace("https://w3id.org/own-pt/nomlex/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSET_PT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")

HAS_TYPE = RDF.type
HAS_LABEL = RDFS.label

TYPE_WORD = OWNPT.Word
TYPE_WORDSENSE = OWNPT.WordSense

NOMLEX_NOUN = NOMELEX.noun
NOMLEX_VERB = NOMELEX.verb

CONTAINS_WORD = OWNPT.word
CONTAINS_WORDSENSE = OWNPT.containsWordSense
CONTAINS_LEXICAL_FORM = OWNPT.lexicalForm


class RepairGraph():
    def __init__(self, graph:Graph):
        self.graph = graph
        self.added_triples = 0
        self.removed_triples = 0


    def repair(self):
        """"""

        # actions to apply
        repair_actions = [
            self.fix_word_blank_nodes,
            self.fix_sense_blank_nodes,
            self.remove_void_words,
            self.expand_sense_words,
            self.add_sense_labels,
            self.add_word_types,
            self.add_sense_types,
            self.add_literal_tag_pt,
            self.remove_word_duplicates,
            self.remove_sense_duplicates,
            self.remove_desconex_sense_nodes,
            self.remove_desconex_word_nodes]

        # apply actions 
        for action in repair_actions:
            # computes added/removed before action
            before_added_triples = self.added_triples
            before_removed_triples = self.removed_triples
            # run action
            action()
            # computes added/removed after action
            after_added_triples = self.added_triples
            after_removed_triples = self.removed_triples
            
            # plots info
            logger.info(f"triples added by action: {after_added_triples - before_added_triples}")
            logger.info(f"triples removed by action: {after_removed_triples - before_removed_triples}")

        # resulting added and removed triples
        logger.info("all actions applied!")
        logger.info(f"total triples added: {self.added_triples}")
        logger.info(f"total triples removed: {self.removed_triples}")


    def remove_desconex_word_nodes(self):
        """"""

        # remove Words without Sense
        logger.debug("searching Words without Sense")
        query = (
            "SELECT ?w "
            "WHERE{{ "
                "{{ ?w {haslexical} ?l . }} UNION "
                "{{ ?w {hastype} {typeword} . }}"
            "FILTER NOT EXISTS {{ "
                "{{ ?s {hasword} ?w . }} UNION  "
                "{{ ?s {nomlexnoum} ?w . }} UNION "
                "{{ ?s {nomlexverb} ?w . }} }} }} ")
        result = self.graph.query(query.format(
                    hastype = HAS_TYPE.n3(),
                    hasword = CONTAINS_WORD.n3(),
                    typeword = TYPE_WORD.n3(),
                    haslexical = CONTAINS_LEXICAL_FORM.n3(),
                    nomlexnoum = NOMLEX_NOUN.n3(),
                    nomlexverb = NOMLEX_VERB.n3()))
        
        # drop node
        logger.info(f"removing Words without Sense (actions to apply: {len(result)})")
        for word, in result:
            self._drop_node(word, "remove_desconex_word_nodes")


    def remove_desconex_sense_nodes(self):
        """"""

        # remove Senses without a Synset 
        logger.debug("searching Senses without Synset")
        query = (
            "SELECT ?s "
            "WHERE{{ "
                "{{ ?s {hasword} ?w . }} UNION "
                "{{ ?s {hastype} {typesense} . }}"
            "FILTER NOT EXISTS {{ "
                "{{ ?ss {hassense} ?s . }} }} }} ")
        result = self.graph.query(query.format(
                    hastype = HAS_TYPE.n3(),
                    hasword = CONTAINS_WORD.n3(),
                    hassense = CONTAINS_WORDSENSE.n3(),
                    typesense = TYPE_WORDSENSE.n3()))
        
        # drop node
        logger.info(f"removing Senses without Synset (actions to apply: {len(result)})")
        for sense, in result:
            self._drop_node(sense, "remove_desconex_sense_nodes")


    def remove_sense_duplicates(self):
        """"""

        # replace Senses with same label from same Synset
        logger.debug("searching Senses with same label Synset")
        query = (
            "SELECT ?s1 ?s2 "
            "WHERE{{ "
            "?s1 {haslabel} ?l . ?ss {hassense} ?s1 . "
            "?s2 {haslabel} ?l . ?ss {hassense} ?s2 . "
            "FILTER (?s1 != ?s2) }}")
        result = self.graph.query(query.format(
                    haslabel = HAS_LABEL.n3(),
                    hassense = CONTAINS_WORDSENSE.n3()))
        
        # just replaces nodes
        logger.info(f"unifying Senses with same label Synset (actions to apply: {len(result)})")
        for word1, word2 in result:
            self._replace_node(word2, word1, "remove_sense_duplicates")


    def remove_word_duplicates(self):
        """"""

        # replace Words with same LexicalForm
        logger.debug("searching Words with same LexicalForm")
        query = (
            "SELECT ?w1 ?w2 "
            "WHERE{{"
            "?w1 {lexical} ?l ."
            "?w2 {lexical} ?l ."
            "FILTER (?w1 != ?w2) }}")
        result = self.graph.query(query.format(
                    lexical = CONTAINS_LEXICAL_FORM.n3()))
        
        # just replaces nodes
        logger.info(f"unifying Words with same LexicalForm (actions to apply: {len(result)})")
        for word1, word2 in result:
            self._replace_node(word2, word1, "remove_word_duplicates")


    def add_literal_tag_pt(self):
        """"""

        # find and fix Literal without @pt tag
        logger.debug("searching lexicalForms and labels without '@pt' tag")
        query = (
            "SELECT ?s ?p ?w "
            "WHERE{{ "
                "{{ ?s ?p ?w . FILTER (?p = {haslabel}) }} UNION "
                "{{ ?s ?p ?w . FILTER (?p = {haslexical}) }} "
            "FILTER ( lang(?w) != 'pt') }}")
        result = self.graph.query(query.format(
                    haslabel = HAS_LABEL.n3(),
                    haslexical = CONTAINS_LEXICAL_FORM.n3()))
        
        # just add tripples
        logger.info(f"adding '@pt' tag (actions to apply: {len(result)})")
        for s, p, lexical in result:
            new_lexical = Literal(lexical.toPython(), lang="pt")
            self._add_triple((s,p,new_lexical), "add_literal_tag_pt")
            self._drop_triple((s, p, lexical), "add_literal_tag_pt")


    def add_word_types(self):
        """"""

        # find and fix Word without type
        logger.debug("searching Words without type")
        query = (
            "SELECT ?s ?w "
            "WHERE{{ ?s {hasword} ?w ."
            "FILTER NOT EXISTS {{ ?w {hastype} ?t .}} }}")
        result = self.graph.query(query.format(
                    hastype = HAS_TYPE.n3(),
                    hasword = CONTAINS_WORD.n3()))
        
        # just add tripples
        logger.info(f"typing Words (actions to apply: {len(result)})")
        for _, word in result:
            self._add_triple((word, HAS_TYPE, TYPE_WORD), "add_word_types")
            # self.graph.add((word, HAS_TYPE, TYPE_WORD))


    def add_sense_types(self):
        """"""

        # find and fix Sense without type
        logger.debug("searching WordSenses without type")
        query = (
            "SELECT ?ss ?s "
            "WHERE{{ "
            "{{ ?ss {hassense} ?s . }} "
            "FILTER NOT EXISTS {{ ?s {hastype} ?t .}} }}")
        result = self.graph.query(query.format(
                    hastype = HAS_TYPE.n3(),
                    hassense = CONTAINS_WORDSENSE.n3()))
        
        # just add tripples
        logger.info(f"typing WordSenses (actions to apply: {len(result)})")
        for _, sense in result:
            self._add_triple((sense, HAS_TYPE, TYPE_WORDSENSE), "add_sense_types")
            # self.graph.add((sense, HAS_TYPE, TYPE_WORDSENSE))


    def add_sense_labels(self):
        """"""

        # find expand Senses without Word by label
        logger.debug("searching Senses without label")
        query = (
            "SELECT ?ss ?s "
            "WHERE{{ ?ss {hassense} ?s ."
            "FILTER NOT EXISTS {{ ?s {haslabel} ?l .}} }}")
        result = self.graph.query(query.format(
                    haslabel = HAS_LABEL.n3(),
                    hassense = CONTAINS_WORDSENSE.n3()))
        
        # create label based on Word/LexicalForm
        logger.info(f"labelling Senses (actions to apply: {len(result)})")
        for _, sense in result:
            word = self.graph.value(sense, CONTAINS_WORD)
            label = self.graph.value(word, CONTAINS_LEXICAL_FORM)
            label = Literal(label.toPython())
            self._add_triple((sense, HAS_LABEL, label), "add_sense_labels")
            # self.graph.add((sense, HAS_LABEL, label))


    def expand_sense_words(self):
        """"""

        # find expand Senses without Word by label
        logger.debug("searching Senses without Word")
        query = (
            "SELECT ?ss ?s "
            "WHERE{{ ?ss {hassense} ?s ."
            "FILTER NOT EXISTS {{ ?s {hasword} ?w .}} }}")
        result = self.graph.query(query.format(
                    hasword = CONTAINS_WORD.n3(),
                    hassense = CONTAINS_WORDSENSE.n3()))
        
        # create word, lexicalform and connect
        logger.info(f"expanding Senses without Word (actions to apply: {len(result)})")
        for _, sense in result:
            word = self._word_by_sense(sense, True)
            self._add_triple((sense, CONTAINS_WORD, word), "expand_sense_words")
            # self.graph.add((sense, CONTAINS_WORD, word))


    def remove_void_words(self):
        """"""
        
        # find and remove Words without LexicalForm
        logger.debug("searching Words without LexicalForm")
        query = (
            "SELECT ?s ?w "
            "WHERE{{ ?s {hasword} ?w ."
            "FILTER NOT EXISTS {{ ?w {lexical} ?wl .}} }}")
        result = self.graph.query(query.format(
                    hasword = CONTAINS_WORD.n3(),
                    lexical = CONTAINS_LEXICAL_FORM.n3()))
        
        # remove connection from WordSense to Word
        logger.info(f"removing Words without LexicalForm (actions to apply: {len(result)})")
        for sense, word in result:
            self._drop_triple((sense, CONTAINS_WORD, word), "remove_void_words")
            # self.graph.remove((sense, CONTAINS_WORD, word))


    def fix_word_blank_nodes(self):
        """"""
        
        # searching BlankNode Word's
        logger.debug("searching Word BlankNodes")
        query = (
            "SELECT ?s ?o "
            "WHERE {{ ?s {predicate} ?o . FILTER (isBlank(?o)) }}")
        result = self.graph.query(query.format(
                    predicate = CONTAINS_WORD.n3()))

        # replace BlankNode Word's
        logger.info(f"replacing Word BlankNodes (actions to apply: {len(result)})")
        for sense, word in result:
            new_word = self._word_uri(sense, word)
            if new_word is not None:
                self._replace_node(word, new_word, "fix_word_blank_nodes")
            else:
                logger.warning(f"could not replace {word.n3()} from sense {sense.n3()}")


    def fix_sense_blank_nodes(self):
        """"""
        
        # searching BlankNode WordSense's
        logger.debug("searching WordSense BlankNodes")
        query = (
            "SELECT ?s ?o "
            "WHERE {{ ?s {predicate} ?o . FILTER (isBlank(?o)) }}")
        result = self.graph.query(query.format(
                    predicate = CONTAINS_WORDSENSE.n3()))

        # replace BlankNode WordSense's
        logger.info(f"replacing WordSense BlankNodes (actions to apply: {len(result)})")
        for synset, sense in result:
            new_sense = self._new_sense(synset, sense)
            self._replace_node(sense, new_sense, "fix_sense_blank_nodes")


    def _new_sense(self, synset, sense):
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
        
        return new_sense


    def _word_uri(self, sense, word):
        """"""

        # if word has lexical form
        lexical_form = self.graph.value(word, CONTAINS_LEXICAL_FORM)
        if lexical_form is not None:
            lexical_form = lexical_form.toPython()
            return self._new_word(lexical_form)

        # otherwise
        return self._word_by_sense(sense)


    def _get_word(self, lexical_form:str):
        """"""

        lexical_form = Literal(lexical_form, lang="pt")
        return self.graph.value(predicate=CONTAINS_LEXICAL_FORM, object=lexical_form)


    def _new_word(self, lexical_form:str, add_lexical=False):
        """"""

        word = WORD[lexical_form.replace(" ", "_")]
        if add_lexical:
            lexical_form = Literal(lexical_form, lang="pt")
            self._add_triple((word, CONTAINS_LEXICAL_FORM, lexical_form), "new_word")
            # self.graph.add((word, CONTAINS_LEXICAL_FORM, lexical_form))

        return word


    def _word_by_sense(self, sense, add_lexical=False):
        """"""

        # if sense has lexical form on label
        sense_label = self.graph.value(sense, HAS_LABEL)
        if sense_label is not None:
            # searchs a suitable word on graph
            sense_label = sense_label.toPython()
            word = self._get_word(sense_label)
            
            if word is not None:return word

            # defines new suitable word
            return self._new_word(sense_label, add_lexical)
        
        # otherwise
        return None


    def _replace_node(self, old_node, new_node, prefix="replace"):
        """"""

        logger.debug(f"{prefix}:replacing node '{old_node.n3()}' by '{new_node.n3()}'")

        # replaces objects
        result = self.graph.subject_predicates(old_node)
        for s,p in result:
            self._add_triple((s,p,new_node), prefix)
            self._drop_triple((s,p,old_node), prefix)
            # self.graph.add((s,p,new_node))
            # self.graph.remove((s,p,old_node))
        
        # replaces subjects
        result = self.graph.predicate_objects(old_node)
        for p, o in result:
            self._add_triple((new_node,p,o), prefix)
            self._drop_triple((old_node,p,o), prefix)
            # self.graph.add((new_node,p,o))
            # self.graph.remove((old_node,p,o))


    def _drop_node(self, node, prefix="drop_node"):
        """"""
        
        logger.debug(f"{prefix}:dropping node '{node.n3()}'")

        # self.graph.remove((node,None,None))
        # self.graph.remove((None,None,node))
        for triple in self.graph.triples((node,None,None)):
            self._drop_triple(triple, prefix)
        for triple in self.graph.triples((None,None,node)):
            self._drop_triple(triple, prefix)


    def _add_triple(self, triple, prefix="add_triple"):
        s,p,o = triple
        logger.debug(f"{prefix}:adding triple: {s.n3()} {p.n3()} {o.n3()}")
        self.graph.add(triple)

        # count triples added
        self.added_triples += 1

    def _drop_triple(self, triple, prefix="drop_triple"):
        s,p,o = triple
        logger.debug(f"{prefix}:removing triple: {s.n3()} {p.n3()} {o.n3()}")
        self.graph.remove(triple)

        # count triples removed
        self.removed_triples += 1