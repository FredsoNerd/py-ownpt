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


def remove_desconex_word_nodes(ownpt:Graph):
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
    result = ownpt.query(query.format(
                hastype = HAS_TYPE.n3(),
                hasword = CONTAINS_WORD.n3(),
                typeword = TYPE_WORD.n3(),
                haslexical = CONTAINS_LEXICAL_FORM.n3(),
                nomlexnoum = NOMLEX_NOUN.n3(),
                nomlexverb = NOMLEX_VERB.n3()))
    
    # drop node
    logger.info(f"removing Words without Sense (actions to apply: {len(result)})")
    for word, in result:
        _drop_node(ownpt, word, "remove_desconex_word_nodes")


def remove_desconex_sense_nodes(ownpt:Graph):
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
    result = ownpt.query(query.format(
                hastype = HAS_TYPE.n3(),
                hasword = CONTAINS_WORD.n3(),
                hassense = CONTAINS_WORDSENSE.n3(),
                typesense = TYPE_WORDSENSE.n3()))
    
    # drop node
    logger.info(f"removing Senses without Synset (actions to apply: {len(result)})")
    for sense, in result:
        _drop_node(ownpt, sense, "remove_desconex_sense_nodes")


def remove_sense_duplicates(ownpt:Graph):
    """"""

    # replace Senses with same label from same Synset
    logger.debug("searching Senses with same label Synset")
    query = (
        "SELECT ?s1 ?s2 "
        "WHERE{{ "
        "?s1 {haslabel} ?l . ?ss {hassense} ?s1 . "
        "?s2 {haslabel} ?l . ?ss {hassense} ?s2 . "
        "FILTER (?s1 != ?s2) }}")
    result = ownpt.query(query.format(
                haslabel = HAS_LABEL.n3(),
                hassense = CONTAINS_WORDSENSE.n3()))
    
    # just replaces nodes
    logger.info(f"unifying Senses with same label Synset (actions to apply: {len(result)})")
    for word1, word2 in result:
        _replace_node(ownpt, word2, word1, "remove_sense_duplicates")


def remove_word_duplicates(ownpt:Graph):
    """"""

    # replace Words with same LexicalForm
    logger.debug("searching Words with same LexicalForm")
    query = (
        "SELECT ?w1 ?w2 "
        "WHERE{{"
        "?w1 {lexical} ?l ."
        "?w2 {lexical} ?l ."
        "FILTER (?w1 != ?w2) }}")
    result = ownpt.query(query.format(
                lexical = CONTAINS_LEXICAL_FORM.n3()))
    
    # just replaces nodes
    logger.info(f"unifying Words with same LexicalForm (actions to apply: {len(result)})")
    for word1, word2 in result:
        _replace_node(ownpt, word2, word1, "remove_word_duplicates")


def add_word_types(ownpt:Graph):
    """"""

    # find and fix Word without type
    logger.debug("searching Words without type")
    query = (
        "SELECT ?s ?w "
        "WHERE{{ ?s {hasword} ?w ."
        "FILTER NOT EXISTS {{ ?w {hastype} ?t .}} }}")
    result = ownpt.query(query.format(
                hastype = HAS_TYPE.n3(),
                hasword = CONTAINS_WORD.n3()))
    
    # just add tripples
    logger.info(f"typing Words (actions to apply: {len(result)})")
    for _, word in result:
        _add_triple(ownpt, (word, HAS_TYPE, TYPE_WORD), "add_word_types")
        # ownpt.add((word, HAS_TYPE, TYPE_WORD))


def add_sense_types(ownpt:Graph):
    """"""

    # find and fix Sense without type
    logger.debug("searching WordSenses without type")
    query = (
        "SELECT ?ss ?s "
        "WHERE{{ "
        "{{ ?ss {hassense} ?s . }} "
        "FILTER NOT EXISTS {{ ?s {hastype} ?t .}} }}")
    result = ownpt.query(query.format(
                hastype = HAS_TYPE.n3(),
                hassense = CONTAINS_WORDSENSE.n3()))
    
    # just add tripples
    logger.info(f"typing WordSenses (actions to apply: {len(result)})")
    for _, sense in result:
        _add_triple(ownpt, (sense, HAS_TYPE, TYPE_WORDSENSE), "add_sense_types")
        # ownpt.add((sense, HAS_TYPE, TYPE_WORDSENSE))


def add_sense_labels(ownpt:Graph):
    """"""

    # find expand Senses without Word by label
    logger.debug("searching Senses without label")
    query = (
        "SELECT ?ss ?s "
        "WHERE{{ ?ss {hassense} ?s ."
        "FILTER NOT EXISTS {{ ?s {haslabel} ?l .}} }}")
    result = ownpt.query(query.format(
                haslabel = HAS_LABEL.n3(),
                hassense = CONTAINS_WORDSENSE.n3()))
    
    # create label based on Word/LexicalForm
    logger.info(f"labelling Senses (actions to apply: {len(result)})")
    for _, sense in result:
        word = ownpt.value(sense, CONTAINS_WORD)
        label = ownpt.value(word, CONTAINS_LEXICAL_FORM)
        label = Literal(label.toPython())
        _add_triple(ownpt, (sense, HAS_LABEL, label), "add_sense_labels")
        # ownpt.add((sense, HAS_LABEL, label))


def expand_sense_words(ownpt:Graph):
    """"""

    # find expand Senses without Word by label
    logger.debug("searching Senses without Word")
    query = (
        "SELECT ?ss ?s "
        "WHERE{{ ?ss {hassense} ?s ."
        "FILTER NOT EXISTS {{ ?s {hasword} ?w .}} }}")
    result = ownpt.query(query.format(
                hasword = CONTAINS_WORD.n3(),
                hassense = CONTAINS_WORDSENSE.n3()))
    
    # create word, lexicalform and connect
    logger.info(f"expanding Senses without Word (actions to apply: {len(result)})")
    for _, sense in result:
        word = _word_by_sense(ownpt, sense, True)
        _add_triple(ownpt, (sense, CONTAINS_WORD, word), "expand_sense_words")
        # ownpt.add((sense, CONTAINS_WORD, word))


def remove_void_words(ownpt:Graph):
    """"""
    
    # find and remove Words without LexicalForm
    logger.debug("searching Words without LexicalForm")
    query = (
        "SELECT ?s ?w "
        "WHERE{{ ?s {hasword} ?w ."
        "FILTER NOT EXISTS {{ ?w {lexical} ?wl .}} }}")
    result = ownpt.query(query.format(
                hasword = CONTAINS_WORD.n3(),
                lexical = CONTAINS_LEXICAL_FORM.n3()))
    
    # remove connection from WordSense to Word
    logger.info(f"removing Words without LexicalForm (actions to apply: {len(result)})")
    for sense, word in result:
        _drop_triple(ownpt, (sense, CONTAINS_WORD, word), "remove_void_words")
        # ownpt.remove((sense, CONTAINS_WORD, word))


def fix_word_blank_nodes(ownpt:Graph):
    """"""
    
    # searching BlankNode Word's
    logger.debug("searching Word BlankNodes")
    query = (
        "SELECT ?s ?o "
        "WHERE {{ ?s {predicate} ?o . FILTER (isBlank(?o)) }}")
    result = ownpt.query(query.format(
                predicate = CONTAINS_WORD.n3()))

    # replace BlankNode Word's
    logger.info(f"replacing Word BlankNodes (actions to apply: {len(result)})")
    for sense, word in result:
        new_word = _word_uri(ownpt, sense, word)
        if new_word is not None:
            _replace_node(ownpt, word, new_word, "fix_word_blank_nodes")
        else:
            logger.warning(f"could not replace {word.n3()} from sense {sense.n3()}")


def fix_sense_blank_nodes(ownpt:Graph):
    """"""
    
    # searching BlankNode WordSense's
    logger.debug("searching WordSense BlankNodes")
    query = (
        "SELECT ?s ?o "
        "WHERE {{ ?s {predicate} ?o . FILTER (isBlank(?o)) }}")
    result = ownpt.query(query.format(
                predicate = CONTAINS_WORDSENSE.n3()))

    # replace BlankNode WordSense's
    logger.info(f"replacing WordSense BlankNodes (actions to apply: {len(result)})")
    for synset, sense in result:
        new_sense = _new_sense(ownpt, synset, sense)
        _replace_node(ownpt, sense, new_sense, "fix_sense_blank_nodes")


def _new_sense(ownpt, synset, sense):
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
        if new_triple not in ownpt:
            break
        
        # update counter
        sense_id += 1
    
    return new_sense


def _word_uri(ownpt, sense, word):
    """"""

    # if word has lexical form
    lexical_form = ownpt.value(word, CONTAINS_LEXICAL_FORM)
    if lexical_form is not None:
        lexical_form = lexical_form.toPython()
        return _new_word(ownpt, lexical_form)

    # otherwise
    return _word_by_sense(ownpt, sense)


def _get_word(ownpt, lexical_form:str):
    """"""

    lexical_form = Literal(lexical_form, lang="pt")
    return ownpt.value(predicate=CONTAINS_LEXICAL_FORM, object=lexical_form)


def _new_word(ownpt, lexical_form:str, add_lexical=False):
    """"""

    word = WORD[lexical_form.replace(" ", "_")]
    if add_lexical:
        lexical_form = Literal(lexical_form, lang="pt")
        _add_triple(ownpt, (word, CONTAINS_LEXICAL_FORM, lexical_form), "new_word")
        # ownpt.add((word, CONTAINS_LEXICAL_FORM, lexical_form))

    return word


def _word_by_sense(ownpt, sense, add_lexical=False):
    """"""

    # if sense has lexical form on label
    sense_label = ownpt.value(sense, HAS_LABEL)
    if sense_label is not None:
        # searchs a suitable word on graph
        sense_label = sense_label.toPython()
        word = _get_word(ownpt, sense_label)
        
        if word is not None:return word

        # defines new suitable word
        return _new_word(ownpt, sense_label, add_lexical)
    
    # otherwise
    return None


def _replace_node(ownpt, old_node, new_node, prefix="replace"):
    """"""

    logger.debug(f"{prefix}:repacing node '{old_node.n3()}' by '{new_node.n3()}'")

    # replaces objects
    result = ownpt.subject_predicates(old_node)
    for s,p in result:
        _add_triple(ownpt, (s,p,new_node), prefix)
        _drop_triple(ownpt, (s,p,old_node), prefix)
        # ownpt.add((s,p,new_node))
        # ownpt.remove((s,p,old_node))
    
    # replaces subjects
    result = ownpt.predicate_objects(old_node)
    for p, o in result:
        _add_triple(ownpt, (new_node,p,o), prefix)
        _drop_triple(ownpt, (old_node,p,o), prefix)
        # ownpt.add((new_node,p,o))
        # ownpt.remove((old_node,p,o))


def _drop_node(ownpt, node, prefix="drop_node"):
    """"""
    
    logger.debug(f"{prefix}:dropping node '{node.n3()}'")

    # ownpt.remove((node,None,None))
    # ownpt.remove((None,None,node))
    for triple in ownpt.triples((node,None,None)):
        _drop_triple(ownpt, triple, prefix)
    for triple in ownpt.triples((None,None,node)):
        _drop_triple(ownpt, triple, prefix)


def _add_triple(ownpt, triple, prefix="add_triple"):
    s,p,o = triple
    logger.debug(f"{prefix}:adding triple: {s.n3()} {p.n3()} {o.n3()}")
    ownpt.add(triple)

def _drop_triple(ownpt, triple, prefix="drop_triple"):
    s,p,o = triple
    logger.debug(f"{prefix}:removing triple: {s.n3()} {p.n3()} {o.n3()}")
    ownpt.remove(triple)