# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from rdflib import Graph, Namespace, URIRef, BNode
from rdflib import Literal, XSD, RDF, RDFS, SKOS, OWL

# global
OWNPT = Namespace("https://w3id.org/own-pt/wn30/schema/")
NOMLEX = Namespace("https://w3id.org/own-pt/nomlex/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSET_PT = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")


def update_ownpt_from_dump(ownpt:Graph, wn:dict):
    """"""

    # removing WordSense from Synset
    ownpt.remove((None, OWNPT.containsWordSense, None))
    # removing properties of WordSense
    ownpt.remove((None, RDF.type, OWNPT.WordSense))
    ownpt.remove((None, OWNPT.wordNumber, None))
    ownpt.remove((None, RDFS.label, None))
    # removing Word from WordSense
    ownpt.remove((None, OWNPT.word, None))
    # removing properties of Word
    ownpt.remove((None, RDF.type, OWNPT.Word))
    ownpt.remove((None, OWNPT.lexicalForm, None))

    # removing gloss from from Synset
    ownpt.remove((None, OWNPT.gloss, None))

    # removing example from from Synset
    ownpt.remove((None, OWNPT.example, None))

    # removing antonymOf
    ownpt.remove((None, OWNPT.antonymOf, None))
    
    # updates synsets
    for synset in wn:
        _update_synset(ownpt, synset)

    # update relations
    pointers_uri_map = {"wn30_pt_antonymOf":OWNPT.antonymOf}
    _update_pointers(ownpt, wn, pointers_uri_map)

    return ownpt


def update_morpho_from_dump(wn:dict):
    """"""
    
    ownpt = Graph()

    # morphosemantic links
    pointers_uri_map = {  
        "wn30_pt_property": NOMLEX.property,
        "wn30_pt_result": NOMLEX.result,
        "wn30_pt_state": NOMLEX.state,
        "wn30_pt_undergoer": NOMLEX.undergoer,
        "wn30_pt_uses": NOMLEX.uses,
        "wn30_pt_vehicle": NOMLEX.vehicle,
        "wn30_pt_event": NOMLEX.event,
        "wn30_pt_instrument": NOMLEX.instrument,
        "wn30_pt_location": NOMLEX.location,
        "wn30_pt_material": NOMLEX.material,
        "wn30_pt_agent": NOMLEX.agent,
        "wn30_pt_bodyPart": NOMLEX.bodyPart,
        "wn30_pt_byMeansOf": NOMLEX.byMeansOf
    }

    # update links
    _update_pointers(ownpt, wn, pointers_uri_map)
    
    return ownpt


def dump_update(
    doc_wn = [],
    doc_suggestions = [],
    doc_votes = [],
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2):
    """"""

    # acesses only sources
    wn = [item["_source"] for item in doc_wn]
    votes = [item["_source"] for item in doc_votes]
    suggestions = [item["_source"] for item in doc_suggestions]

    # filter suggestions
    suggestions = _filter_suggestions(suggestions, votes, users_senior, trashold_senior, trashold_junior)

    # joins synsets and suggestions
    f_idl = lambda x: x["doc_id"]
    f_idr = lambda x: x["doc_id"]
    zipped = _left_zip_by_id(wn, suggestions, f_idl, f_idr)

    # apply suggestions
    for synset, suggestions in zipped:
        _apply_suggestions(synset, suggestions)
    
    return doc_wn


def compare_ownpt_dump(ownpt:Graph, wn:dict):
    """"""

    # compare words
    logger.debug("comparing words...")
    for synset in wn:
        doc_id = synset['doc_id']
        result, words, wordsd, wordso = _compare_words(ownpt, synset)

        if not result:
            logger.warning(f"synset {doc_id} comparing words resulted FALSE")
            logger.debug(f"synset {doc_id} results:"
                            f"\n\twords {wordsd} found only in dump"
                            f"\n\twords {wordso} found only in ownpt"
                            f"\n\twords {words} found in both documents")

            # generate report as jsonl
    
    # compare antonymOf
    logger.debug("comparing relation antonymOf...")
    

def _compare_words(ownpt:Graph, synset:dict):
    """"""  
    compare = True
    
    # report words
    words = []
    wordso = []
    wordsd = synset["word_pt"] if "word_pt" in synset else []

    # finds all wordsenses, and its words
    doc_id = synset["doc_id"]
    synset_uri = SYNSET_PT[doc_id]
    
    query = "SELECT ?wl WHERE{{ {} {} ?s . ?s {} ?w . ?w {} ?wl . }}"
    result = ownpt.query(query.format(
                synset_uri.n3(), OWNPT.containsWordSense.n3(),
                OWNPT.word.n3(), OWNPT.lexicalForm.n3()))
    
    # compares words in synset with dump
    for wordl in result:
        wordl = wordl.toPython().strip()

        # checks if word exists in dump
        if wordl in wordsd:
            words.append(wordl)
            wordsd.remove(wordl)
        else:
            wordso.append(wordl)

    # check if unique words are void
    if len(wordsd) > 0: compare = False
    if len(wordso) > 0: compare = False
    
    return compare, words, wordsd, wordso


def _compare_antonyms(ownpt:Graph, synset:dict):
    pass


def _update_pointers(ownpt:Graph, synsets, pointer_uri_map:dict=dict()):
    """"""

    for pointer, predicate in pointer_uri_map.items():
        _update_pointer(ownpt, synsets, pointer, predicate)


def _update_pointer(ownpt:Graph, synsets, pointer_name:str, predicate:URIRef):
    """"""

    # join pairs
    doc_id_map = {synset["doc_id"]:synset for synset in synsets}
    pairs_sense_id = []
    for source_synset in synsets:
        if pointer_name not in source_synset:
            continue
        for pointer in source_synset[pointer_name]:
            source_senses = _get_wordsenses(source_synset, pointer, "source_word")
            
            target_doc_id = pointer["target_synset"]
            target_synset = doc_id_map[target_doc_id]
            target_senses = _get_wordsenses(target_synset, pointer, "target_word")

            pairs_sense_id += [(s, t) for s in source_senses for t in target_senses]
    
    # add relations
    for source_sense_id, target_sense_id in pairs_sense_id:
        source_wordsense = WORDSENSE[source_sense_id]
        target_wordsense = WORDSENSE[target_sense_id]
        ownpt.add((source_wordsense, predicate, target_wordsense))


def _get_wordsenses(synset, pointer, key):
    """"""
    
    word = pointer[key] if key in pointer else None
    words = synset["word_pt"] if "word_pt" in synset else []
    doc_id = synset["doc_id"]

    # if not source/target word
    if word is None:
        return [f"{doc_id}-{i+1}" for i in range(len(words))]
    # if source/target word in synset
    if word in words:
        return [f"{doc_id}-{1+words.index(word)}"]
    # other cases
    return []


def _update_synset(ownpt:Graph, synset:dict):
    """"""

    doc_id = synset["doc_id"]
    synset_pt = SYNSET_PT[doc_id]
    
    # adding word-pt
    word_pt = synset["word_pt"] if "word_pt" in synset else []
    for i, word in enumerate(word_pt, start=1):
        word_pt = WORD[word.replace(" ", "_")]  
        word_sense = WORDSENSE[f"{doc_id}-{i}"]

        ownpt.add((synset_pt, OWNPT.containsWordSense, word_sense))
        
        # word sense
        ownpt.add((word_sense, RDF.type, OWNPT.WordSense))
        ownpt.add((word_sense, OWNPT.wordNumber, Literal(i)))
        ownpt.add((word_sense, RDFS.label, Literal(word, lang="pt")))

        # word form
        ownpt.add((word_sense, OWNPT.word, word_pt))
        ownpt.add((word_pt, RDF.type, OWNPT.Word))
        ownpt.add((word_pt, OWNPT.lexicalForm, Literal(word, lang="pt")))


    # adding gloss-pt
    gloss_pt = synset["gloss_pt"] if "gloss_pt" in synset else []
    for i, gloss in enumerate(gloss_pt, start=1):
        ownpt.add((synset_pt, OWNPT.gloss, Literal(gloss, lang="pt")))

    # adding example-pt
    example_pt = synset["example_pt"] if "example_pt" in synset else []
    for i, example in enumerate(example_pt, start=1):
        ownpt.add((synset_pt, OWNPT.example, Literal(example, lang="pt")))


def _apply_suggestions(synset:dict, suggestions:list):
    for suggestion in suggestions:
        _apply_suggestion(synset, suggestion)


def _apply_suggestion(synset:dict, suggestion):
    action = suggestion["action"]
    params = suggestion["params"]

    if action == "add-word-pt":
        _add_parameter(synset, "word_pt", params)
    elif action == "add-gloss-pt":
        _add_parameter(synset, "gloss_pt", params)
    elif action == "add-example-pt":
        _add_parameter(synset, "example_pt", params)
    elif action == "remove-word-pt":
        _remove_parameter(synset, "word_pt", params)
    elif action == "remove-gloss-pt":
        _remove_parameter(synset, "gloss_pt", params)
    elif action == "remove-example-pt":
        _remove_parameter(synset, "example_pt", params)
    else:
        print(f"Not a valid action: {action}")
        # raise Exception(f"Not a valid action: {action}")

    return synset


def _add_parameter(synset, key, params):
    """"""

    if key in synset:
        synset[key].append(params)
    else:
        synset[key] = [params]


def _remove_parameter(synset, key, params):
    """"""

    if key in synset:
        if params in synset[key]:
            synset[key].remove(params)
        else:
            print(f"Param not in synset {synset['doc_id']} key {key}: {params} not in {synset[key]}")
            # raise Exception(f"Param not in synset {synset['doc_id']} key {key}: {params}")
    else:
        print(f"Key not in synset: {key}")
        # raise Exception(f"Key not in synset: {key}")


def _filter_suggestions(
    suggestions:list,
    votes:list,
    users_senior:list,
    trashold_senior:int,
    trashold_junior:int):
    """"""

    # joins suggestions and votes
    f_idl = lambda x: x["id"]
    f_idr = lambda x: x["suggestion_id"]
    zipped = _left_zip_by_id(suggestions, votes, f_idl, f_idr)

    # apply filter rules and return
    return [x[0] for x in zipped if _rules(*x,users_senior,trashold_senior,trashold_junior)]


def _rules(suggestion, votes:list, users_senior:list, trashold_senior:int, trashold_junior:int):
    """"""

    r1 = suggestion["status"] == "new"
    r2 = suggestion["action"] != "comment"
    score = sum([vote["value"] for vote in votes])
    r3 = score >= trashold_senior and suggestion["user"] in users_senior or score >= trashold_junior

    return all([r1,r2,r3])


def _left_zip_by_id(listl, listr, f_idl, f_idr):
    """"""

    # review eficiency
    zipped = {f_idl(l):{"l":l,"r":[]} for l in listl}
    for itemr in listr:
        _id = f_idr(itemr)
        if _id in zipped:
            zipped[_id]["r"].append(itemr)
        else:
            print(f"Got invalid id to zip: {_id}")
            # raise Exception(f"Got invalid id to zip: {_id}")

    return [(item["l"],item["r"]) for item in zipped.values()]
