# -*- coding: utf-8 -*-

from rdflib.util import guess_format

def get_format(filepath:str):
    """"""

    filepath_format = guess_format(filepath, {"jsonld":"json-ld"})    
    return filepath_format if filepath_format else filepath.split(".")[-1]

def get_unify_actions(report:dict):
    for doc, doc_report in report.copy().items():
        if doc_report["compare"]:
            # removes if comparing positive
            report.pop(doc)
        else:
            # adds actions to apply to ownpt
            report[doc]["actions"] = {
                "add-word-pt": report[doc]["word_pt"]["dump"],
                "remove-word-pt": report[doc]["word_pt"]["ownpt"],
                "add-gloss-pt": report[doc]["gloss_pt"]["dump"],
                "remove-gloss-pt": report[doc]["gloss_pt"]["ownpt"],
                "add-example-pt": report[doc]["example_pt"]["dump"],
                "remove-example-pt": report[doc]["example_pt"]["ownpt"]}

    return report