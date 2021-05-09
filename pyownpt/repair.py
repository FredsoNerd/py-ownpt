# -*- coding: utf-8 -*-

import tqdm
import logging
logger = logging.getLogger(__name__)

from rdflib import Graph, Namespace, Literal, RDFS

# global
OWNPT = Namespace("https://w3id.org/own-pt/wn30/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSET_PT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")

HAS_LABEL = RDFS.label

CONTAINS_WORD = OWNPT.word
CONTAINS_WORDSENSE = OWNPT.containsWordSense
CONTAINS_LEXICAL_FORM = OWNPT.lexicalForm


def fix_blank_nodes(ownpt:Graph):
    """"""
    
    # replace BlankNode Word's
    logger.info(f"start replacing BlankNodes type Word")

    query = (
        "SELECT ?s ?o "
        "WHERE {{ ?s {predicate} ?o . FILTER (isBlank(?o)) }}")
    result = ownpt.query(query.format(predicate = CONTAINS_WORD.n3()))

    for sense, word in tqdm.tqdm(result):
        new_word = _get_new_word(ownpt, sense, word)
        if new_word is not None:
            _replace_node(ownpt, word, new_word)
        else:
            logger.warning(f"could not define word for {word.n3()} fom sense {sense.n3( )}")


    # replace BlankNode WordSense's
    logger.info(f"start replacing BlankNodes type WordSense")

    query = (
        "SELECT ?s ?o "
        "WHERE {{ ?s {predicate} ?o . FILTER (isBlank(?o)) }}")
    result = ownpt.query(query.format(predicate = CONTAINS_WORDSENSE.n3()))

    for synset, sense in tqdm.tqdm(result):
        new_sense = _new_sense(ownpt, synset, sense)
        _replace_node(ownpt, sense, new_sense)


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


def _get_new_word(ownpt, sense, word):
    """"""

    # if word has lexical form
    lexical_form = ownpt.value(word, CONTAINS_LEXICAL_FORM)
    if lexical_form is not None:
        lexical_form = lexical_form.toPython()
        return _new_word(ownpt, lexical_form)

    # if sense has lexical form on label
    sense_label = ownpt.value(sense, HAS_LABEL)
    if sense_label is not None:
        # searchs a suitable word on graph
        sense_label = sense_label.toPython()
        word = _get_word(ownpt, sense_label)
        
        if word is not None: return word

        # defines new suitable word
        return _new_word(ownpt, sense_label)
    
    # otherwise
    return None


def _get_word(ownpt, lexical_form:str):
    """"""

    lexical_form = Literal(lexical_form, lang="pt")
    return ownpt.value(predicate=CONTAINS_LEXICAL_FORM, object=lexical_form)


def _new_word(ownpt, lexical_form:str):
    """"""

    word = WORD[lexical_form.replace(" ", "_")]
    lexical_form = Literal(lexical_form, lang="pt")
    ownpt.add((word, CONTAINS_LEXICAL_FORM, lexical_form))

    return word


def _replace_node(ownpt, old_node, new_node):
    """"""

    # replaces objects
    result = ownpt.subject_predicates(old_node)
    for s,p in result:
        ownpt.add((s,p,new_node))
        ownpt.remove((s,p,old_node))
    
    # replaces subjects
    result = ownpt.predicate_objects(old_node)
    for p, o in result:
        ownpt.add((new_node,p,o))
        ownpt.remove((old_node,p,o))
