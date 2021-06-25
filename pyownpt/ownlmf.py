# -*- coding: utf-8 -*-

from posixpath import commonpath
import tqdm
import uuid

from lxml.etree import Element, tostring
from pyownpt.ownpt import Graph, NOMLEX, OWNPT, OWL, SCHEMA, PWN30

class OWNPT_LMF(OWNPT):
    def __init__(self, own_pt:Graph, ili_map:Graph, lexicon_id, label, version,
        lang, status, confidenceScore, url, email, license, citation):

        super().__init__(own_pt)
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
        
        # statistics
        self.statistics = {    
            "senses": 0,
            "synsets": 0,
            "lexical entries": 0,
            "lexical entries pos": 0,
            "sense relations": 0,
            "synset relations": 0,
            "synset examples": 0,
            "synset definitions": 0,}

        # pointers
        self.pointers = {
            SCHEMA.antonymOf:"antonym",
            SCHEMA.seeAlso:"also",
            SCHEMA.participleOf:"participle",
            SCHEMA.adjectivePertainsTo:"pertainym",
            SCHEMA.adverbPertainsTo:"derivation",
            SCHEMA.derivationallyRelated:"derivation",
            SCHEMA.classifiesByRegion:"domain_region",
            SCHEMA.classifiedByRegion:"has_domain_region",
            SCHEMA.classifiesByTopic:"domain_topic",
            SCHEMA.classifiedByTopic:"has_domain_topic",
            SCHEMA.classifiesByUsage:"exemplifies",
            SCHEMA.classifiedByUsage:"is_exemplified_by",

            SCHEMA.hypernymOf:"hypernym",
            SCHEMA.hyponymOf:"hyponym",
            SCHEMA.hasInstance:"instance_hypernym",
            SCHEMA.instanceOf:"instance_hyponym",
            SCHEMA.entails:"entails",
            SCHEMA.causes:"causes",
            SCHEMA.similarTo:"similar",
            SCHEMA.attribute:"attribute",

            SCHEMA.partHolonymOf:"holo_part",
            SCHEMA.partMeronymOf:"mero_part",
            SCHEMA.memberHolonymOf:"holo_member",
            SCHEMA.memberMeronymOf:"mero_member",
            SCHEMA.substanceHolonymOf:"holo_substance",
            SCHEMA.substanceMeronymOf:"mero_substance",
            SCHEMA.sameVerbGroupAs:"similar", # verb_group

            NOMLEX.agent:"agent", # other
            NOMLEX.bodyPart:"other", 
            NOMLEX.byMeansOf:"other", 
            NOMLEX.destination:"other", 
            NOMLEX.event:"other", 
            NOMLEX.instrument:"instrument", # other
            NOMLEX.location:"location", # other
            NOMLEX.material:"other", 
            NOMLEX.property:"other", 
            NOMLEX.result:"result", # other
            NOMLEX.state:"other", 
            NOMLEX.undergoer:"other", 
            NOMLEX.uses:"other", 
            NOMLEX.vehicle:"other",
        }

        
    def format(self,):
        self.logger.info("start formating lexical resource")

        lexical_resource = Element("LexicalResource", nsmap=self.namespace)
        lexical_resource.append(self.get_lexicon_lmf())

        # prints statistics about formatting
        for statistics, value in self.statistics.items():
            self.logger.info(f"{statistics} formatted: {value}")

        return tostring(lexical_resource, encoding="UTF-8", pretty_print=True, xml_declaration=True,
            doctype="<!DOCTYPE LexicalResource SYSTEM 'http://globalwordnet.github.io/schemas/WN-LMF-1.0.dtd'>").decode()


    def get_lexicon_lmf(self):
        """"""
            
        lexicon = Element("Lexicon", id=self.lexicon_id, label=self.label, status=self.status,
            version=self.version, language=self.lang, confidenceScore=self.confidenceScore,
            url=self.url, email=self.email, license=self.license, citation=self.citation)

        # list of lexical entries (words) in your wordnet
        self.logger.info(f"formatting lexical entries (words)")

        words = self._get_all_words()
        for word, in tqdm.tqdm(words):
            self.statistics["lexical entries"] += 1
            senses = self.graph.subjects(SCHEMA.word, word)
            word_pos = set([self._get_pos(sense) for sense in senses])

            for pos in word_pos:
                self.statistics["lexical entries pos"] += 1
                lexicon.append(self.get_lexical_entry_lmf(word, pos))
        
        # list of synsets in your wordnet
        self.logger.info(f"formatting synsets")

        synsets = self._get_all_synsets()
        for synset, in tqdm.tqdm(synsets):
            synset_lmf = self.get_synset_lmf(synset)

            # adds only if synset has members
            if synset_lmf.get("members") == "": continue
            
            self.statistics["synsets"] += 1
            lexicon.append(synset_lmf)

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
        for definition in definitions:
            self.statistics["synset definitions"] += 1
            definition_lmf = Element("Definition")
            definition_lmf.text = definition.toPython()
            synset_lmf.append(definition_lmf)

        # list of relations for that synset
        relations = self.get_node_relations(synset)
        for _, rel, target in relations:
            # adds only if relation only if target has members
            if self.get_synset_members(target) == "": continue

            self.statistics["synset relations"] += 1
            synset_lmf.append(self.get_node_relation_lmf("SynsetRelation", rel, target))

        # list of examples for that synset
        examples = self.graph.objects(synset, SCHEMA.example)
        for example in examples:
            self.statistics["synset examples"] += 1
            example_lmf = Element("Example")
            example_lmf.text = example.toPython()
            synset_lmf.append(example_lmf)

        # return synset
        return synset_lmf


    def get_node_relations(self, synset):
        relations = []
        for pointer in self.pointers:
            relations += list(self.graph.triples((synset, pointer, None)))

        return relations


    def get_synset_members(self, synset):
        members = self.graph.objects(synset, SCHEMA.containsWordSense)
        members_ids = [self._get_node_id(member) for member in members]
        return " ".join(sorted(members_ids))


    def get_lexical_entry_lmf(self, word, pos):
        """"""

        # lexical_entry and lemma
        word_id = f"word-{pos}-{str(uuid.uuid1())}"
        lexical_entry = Element("LexicalEntry", id=word_id)
        
        lexical_form = self.graph.value(word, SCHEMA.lexicalForm)
        lemma = Element("Lemma", partOfSpeech=pos, writtenForm=lexical_form)
        
        lexical_entry.append(lemma)

        # list of senses for that lexical_entry (word)
        senses = self.graph.subjects(SCHEMA.word, word)
        for sense in senses:
            # adds only if sense has the same POS
            if self._get_pos(sense) == pos:
                self.statistics["senses"] += 1
                lexical_entry.append(self.get_sense_lmf(sense))

        # returs lexical_entry
        return lexical_entry

    
    def get_sense_lmf(self, sense):
        """"""

        # sense_lmf
        sense_id = self._get_node_id(sense)
        synset = self.graph.value(predicate=SCHEMA.containsWordSense, object=sense)
        synset_id = self._get_synset_id(synset)
        sense_lmf = Element("Sense", id=sense_id, synset=synset_id)

        # list of relations for that sense
        relations = self.get_node_relations(sense)
        for _, rel, target in relations:
            self.statistics["sense relations"] += 1
            sense_lmf.append(self.get_node_relation_lmf("SenseRelation", rel, target))
        
        return sense_lmf
    

    def get_node_relation_lmf(self, item_name, relation, target):
        rel_type = self.pointers[relation]
        return self._get_relation_lmf(item_name, target, rel_type, str(relation))
 

    def _get_relation_lmf(self, item_name, target, rel_type, rel_name):
        target_id = self._get_node_suffix(target)
        return Element(item_name, target=target_id, relType=rel_type,
            attrib={"{{{}}}type".format(self.namespace["dc"]):rel_name}) 
        

    def _get_ili(self, synset):
        synset_id = synset.split("synset-")[-1]
        ili = self.ili.value(predicate=OWL.sameAs, object=PWN30[synset_id])
        if ili is None:
            # maybe historical parsing issues
            synset_id = synset_id.replace("a", "s")
            ili = self.ili.value(predicate=OWL.sameAs, object=PWN30[synset_id])

        return ili.split("/")[-1]
        

    def _get_node_id(self, sense):
        return self._get_node_suffix(sense)


    def _get_synset_id(self, synset):
        return self._get_node_suffix(synset)


    def _get_node_suffix(self, node):
        return f"{self.lexicon_id}-{node.split('instances/')[-1]}"

    
    def _get_pos(self, element, separator="wordsense-"):
        return element.split(separator)[-1].split("-")[1]

    
    def _get_all_words(self):
        return self.graph.query("SELECT ?w WHERE { ?w a wn30:Word }")
    
    
    def _get_all_synsets(self):
        return self.graph.query("SELECT ?s WHERE { VALUES ?t { wn30:Synset wn30:AdjectiveSatelliteSynset wn30:AdjectiveSynset wn30:AdverbSynset wn30:NounSynset wn30:VerbSynset } ?s a ?t . }")
        