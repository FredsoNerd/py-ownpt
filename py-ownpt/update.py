# -*- coding: utf-8 -*-

import json
from itertools import groupby

def dump_update(
    filepath_wn:str,
    filepath_suggestions:str,
    filepath_votes:str,
    filepath_output:str="wn_output.json",
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2):
    """"""

    # loads the data    
    doc_wn = [json.loads(line) for line in open(filepath_wn).readlines()]
    doc_votes = [json.loads(line) for line in open(filepath_votes).readlines()]
    doc_suggestions = [json.loads(line) for line in open(filepath_suggestions).readlines()]

    wn = [item["_source"] for item in doc_wn]
    votes = [item["_source"] for item in doc_votes]
    suggestions = [item["_source"] for item in doc_suggestions]

    # filter suggestions
    suggestions = filter_suggestions(suggestions, votes, users_senior, trashold_senior, trashold_junior)

    # joins synsets and suggestions
    f_idl = lambda x: x["doc_id"]
    f_idr = lambda x: x["doc_id"]
    zipped = _left_zip_by_id(wn, suggestions, f_idl, f_idr)

    # apply suggestions
    for synset, suggestions in zipped:
        apply_suggestions(synset, suggestions)
    
    # saves results
    with open(filepath_output, "w") as outfile:
        for item in doc_wn:
            json.dump(item, outfile)
            outfile.write("\n")

def apply_suggestions(synset:dict, suggestions:list):
    for suggestion in suggestions:
        apply_suggestion(synset, suggestion)

def apply_suggestion(synset:dict, suggestion):
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
    if key in synset:
        synset[key].append(params)
    else:
        synset[key] = [params]

def _remove_parameter(synset, key, params):
    if key in synset:
        if params in synset[key]:
            synset[key].remove(params)
        else:
            print(f"Param not in synset {synset['doc_id']} key {key}: {params} not in {synset[key]}")
            # raise Exception(f"Param not in synset {synset['doc_id']} key {key}: {params}")
    else:
        print(f"Key not in synset: {key}")
        # raise Exception(f"Key not in synset: {key}")


def filter_suggestions(
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
    return suggestions



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


# test
dump_update(
    "/home/fredson/openWordnet-PT/dump/wn.json",
    "/home/fredson/openWordnet-PT/dump/suggestion.json",
    "/home/fredson/openWordnet-PT/dump/votes.json",
    "/home/fredson/openWordnet-PT/dump/outfile.json",
    ["arademaker","vcvpaiva"])