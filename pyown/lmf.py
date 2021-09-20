# -*- coding: utf-8 -*-

from tqdm import tqdm
from lxml.etree import Element, tostring
from pyown.own import Graph, OWN, OWL, SCHEMA, PWN30

class LMF(OWN):
    def __init__(self, own:Graph, ili_map:Graph, lexicon_id, label, version,
        lang, status, confidenceScore, url, email, license, citation):

        super().__init__(own, lang)
        self.ili = ili_map
        self.ili.bind("owl", OWL)
        self.namespace = {"dc":"https://globalwordnet.github.io/schemas/dc/"}

        # basic properties
        self.lexicon_id = lexicon_id
        self.label = label
        self.version = version
        self.lang=lang
        self.status=status
        self.confidenceScore=confidenceScore
        self.url=url
        self.email=email
        self.license=license
        self.citation=citation

        
    def format(self,):
        self.logger.info("start formating lexical resource")

        lexical_resource = Element("LexicalResource", nsmap=self.namespace)
        lexical_resource.append(self.get_lexicon_lmf())

        return tostring(lexical_resource, encoding="UTF-8", pretty_print=True, xml_declaration=True,
            doctype="<!DOCTYPE LexicalResource SYSTEM 'http://globalwordnet.github.io/schemas/WN-LMF-1.1.dtd'>").decode()


    def get_lexicon_lmf(self):
        """"""
            
        lexicon = Element("Lexicon", id=self.lexicon_id, label=self.label, status=self.status,
            version=self.version, language=self.lang, confidenceScore=self.confidenceScore,
            url=self.url, email=self.email, license=self.license, citation=self.citation)

        # list of lexical entries (words) in your wordnet
        self.logger.info(f"formatting lexical entries (words)")
        
        words = self._get_all_words()
        words_lmf = []
        for word, in tqdm(words):
            words_lmf.append(self.get_lexical_entry_lmf(word))
        lexicon.extend(sorted(words_lmf, key = lambda x: x.attrib.items()))
        
        # list of synsets in your wordnet
        self.logger.info(f"formatting synsets")

        synsets = self._get_all_synsets()
        synsets_lmf = []
        for synset, in tqdm(synsets):
            synset_lmf = self.get_synset_lmf(synset)
            # adds only if synset has members
            if not synset_lmf.get("members") == "":
                synsets_lmf.append(synset_lmf)
        lexicon.extend(sorted(synsets_lmf, key = lambda x: x.attrib.items()))

        return lexicon


    def get_synset_lmf(self, synset):
        """"""

        sid = self._get_synset_id(synset)
        ili = self._get_ili(synset)
        pos = self._get_pos(synset, "synset-")
        members = self.get_synset_members(synset)
        synset_lmf = Element("Synset", id=sid, ili=ili, partOfSpeech=pos, members=members)

        # list of definitions for that synset
        definitions = self.graph.objects(synset, SCHEMA.gloss)
        definitions_lmf = []
        for definition in definitions:
            definitions_lmf.append(self._get_text_element_lmf("Definition", definition.toPython()))
        synset_lmf.extend(sorted(definitions_lmf, key = lambda x:x.text))

        # list of relations for that synset
        relations = self.get_node_relations(synset)
        relations_lmf = []
        for _, rel, target in relations:
            # adds only if relation only if target has members
            members = self.get_synset_members(target)
            if not members == "":
                relations_lmf.append(self.get_node_relation_lmf("SynsetRelation", rel, target))
        synset_lmf.extend(sorted(relations_lmf, key = lambda x:x.attrib.items()))

        # list of examples for that synset
        examples = self.graph.objects(synset, SCHEMA.example)
        examples_lmf = []
        for example in examples:
            examples_lmf.append(self._get_text_element_lmf("Example", example.toPython()))
        synset_lmf.extend(sorted(examples_lmf, key = lambda x:x.text))

        # return synset
        return synset_lmf


    def get_lexical_entry_lmf(self, word):
        """"""

        written_form = self.graph.value(word, SCHEMA.lemma)
        part_of_speech = self.graph.value(word, SCHEMA.pos)

        # formatting lexical_entry
        word_id = word.replace(self.WORD, "")
        word_id = f"{self.lexicon_id}-word-{word_id}"
        lexical_entry = Element("LexicalEntry", id=word_id)
        
        # formatting lemma
        lemma = Element("Lemma", partOfSpeech=part_of_speech, writtenForm=written_form)
        lexical_entry.append(lemma)

        # list of other forms for that lexical_entry (word)
        forms = self.graph.objects(word, SCHEMA.otherForm)
        forms_lmf = []
        for form in forms:
            form_lmf = Element("Form", writtenForm=form.toPython()) 
            forms_lmf.append(form_lmf)
        lexical_entry.extend(sorted(forms_lmf, key = lambda x:x.get('writtenForm')))

        # list of senses for that lexical_entry (word)
        senses = self.graph.subjects(SCHEMA.word, word)
        senses_lmf = []
        for sense in senses:
            senses_lmf.append(self.get_sense_lmf(sense))
        lexical_entry.extend(sorted(senses_lmf, key = lambda x:x.attrib.items()))
        
        # list of syntactic behaviours (frame) for that lexical_entry (word)
        behaviours = self.get_syntactic_behaviours(senses)
        behaviours_lmf = []
        for behaviour in behaviours:
            behaviour_lmf = Element("SyntacticBehaviour", subcategorizationFrame=behaviour.toPython())
            behaviours_lmf.append(behaviour_lmf)
        lexical_entry.extend(sorted(behaviours_lmf, key = lambda x:x.get('subcategorizationFrame')))

        # returs lexical_entry
        return lexical_entry

    
    def get_sense_lmf(self, sense):
        """"""

        # sense_lmf
        sense_id = self._get_node_id(sense)
        synset = self.graph.value(predicate=SCHEMA.containsWordSense, object=sense)
        synset_id = self._get_synset_id(synset)
        sense_lmf = Element("Sense", id=sense_id, synset=synset_id)
        
        # if sense has adjective marker
        marker = self.graph.value(sense, SCHEMA.adjPosition)
        if marker is not None:
            sense_lmf.attrib["adjposition"] = marker.toPython()

        # list of relations for that sense
        relations = self.get_node_relations(sense)
        relations_lmf = []
        for _, rel, target in relations:
            relations_lmf.append(self.get_node_relation_lmf("SenseRelation", rel, target))
        sense_lmf.extend(sorted(relations_lmf, key = lambda x:x.attrib.items()))

        # list of examples for that sense
        examples = self.graph.objects(sense, SCHEMA.example)
        examples_lmf = []
        for example in examples:
            examples_lmf.append(self._get_text_element_lmf("Example", example.toPython()))
        sense_lmf.extend(sorted(examples_lmf, key = lambda x:x.text))
        
        return sense_lmf


    def get_syntactic_behaviours(self, senses):
        behaviours = []
        for sense in senses:
            synset = self.graph.value(predicate=SCHEMA.containsWordSense, object=sense)
            behaviours.extend(list(self.graph.objects(synset, SCHEMA.frame)))
        return behaviours


    def get_synset_members(self, synset):
        members = self.graph.objects(synset, SCHEMA.containsWordSense)
        members_ids = [self._get_node_id(member) for member in members]
        return " ".join(sorted(members_ids))
    

    def get_node_relations(self, synset):
        relations = []
        for pointer in self.pointers:
            relations.extend(list(self.graph.triples((synset, pointer, None))))

        return relations


    def get_node_relation_lmf(self, item_name, relation, target):
        rel_type = self.pointers[relation]
        return self._get_relation_lmf(item_name, target, rel_type, str(relation))
 

    def _get_relation_lmf(self, item_name, target, rel_type, rel_name):
        target_id = self._get_node_suffix(target)
        return Element(item_name, target=target_id, relType=rel_type,
            attrib={"{{{}}}type".format(self.namespace["dc"]):rel_name})
        
    
    def _get_text_element_lmf(self, element_name, text):
        element_lmf = Element(element_name)
        element_lmf.text = text
        return element_lmf


    def _get_ili(self, synset):
        synset_id = synset.split("synset-")[-1]
        ili = self.ili.value(predicate=OWL.sameAs, object=PWN30[synset_id])
        if ili is None:
            # maybe historical parsing issues
            synset_id = synset_id.replace("a", "s")
            ili = self.ili.value(predicate=OWL.sameAs, object=PWN30[synset_id])

        return ili.split("/")[-1]


    def sort_element(self, root):
        return self._sort_children(root)


    def _sort_children(self, node):
        if isinstance(node.tag, str):
            node[:] = sorted(node, key = self._get_node_key)
            for child in node:
                self._sort_children(child)


    def _get_node_key(self, node):
        return "{}-{}".format(node.tag, node.attrib)
