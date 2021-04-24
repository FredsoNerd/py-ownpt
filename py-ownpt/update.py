# -*- coding: utf-8 -*-

from json import loads, dump

def cli_dump_update(
    wn_filepath:str,
    suggestions_filepath:str,
    votes_filepath:str,
    output_filepath:str,
    users_senior=[],
    trashold_senior=1,
    trashold_junior=2):
    """"""

    # loads the data    
    doc_wn = _read_jsonl(wn_filepath)
    doc_votes = _read_jsonl(votes_filepath)
    doc_suggestions = _read_jsonl(suggestions_filepath)

    # updates wn docs
    dump_update(doc_wn, doc_suggestions, doc_votes, users_senior, trashold_senior, trashold_junior)

    # saves results
    _write_jsonl(doc_wn, output_filepath)


def cli_update_ownpt_from_dump(
    ownpt_filapath:str,
    wn_filepath:str,
    ownpt_format:str="nt",
    output_filepath:str="output.xml",
    output_format:str="xml"):
    """"""

    wn = [item["_source"] for item in _read_jsonl(wn_filepath)]
    ownpt = Graph().parse(ownpt_filapath, format=ownpt_format)
    update_ownpt_from_dump(ownpt, wn)

    # saves results
    ownpt.serialize(output_filepath, format=output_format, encoding="utf8")


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
    suggestions = filter_suggestions(suggestions, votes, users_senior, trashold_senior, trashold_junior)

    # joins synsets and suggestions
    f_idl = lambda x: x["doc_id"]
    f_idr = lambda x: x["doc_id"]
    zipped = _left_zip_by_id(wn, suggestions, f_idl, f_idr)

    # apply suggestions
    for synset, suggestions in zipped:
        apply_suggestions(synset, suggestions)
    
    return doc_wn

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


def _read_jsonl(filepath):
    return [loads(line) for line in open(filepath).readlines()]

def _write_jsonl(items, filepath):
    outfile = open(filepath, "w")
    for item in items:
        dump(item, outfile)
        outfile.write("\n")

# test
cli_dump_update(
    "/home/fredson/openWordnet-PT/dump/wn.json",
    "/home/fredson/openWordnet-PT/dump/suggestion.json",
    "/home/fredson/openWordnet-PT/dump/votes.json",
    "/home/fredson/openWordnet-PT/dump/outfile.json",
    ["arademaker","vcvpaiva"])
