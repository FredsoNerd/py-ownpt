# -*- coding: utf-8 -*-

from posixpath import commonpath
import tqdm
import uuid

from lxml.etree import Element, tostring
from pyownpt.ownpt import Graph, NOMLEX, OWNPT, OWL, SCHEMA, PWN30

class OWNPT_LMF(OWNPT):
    def __init__(self, own_pt:Graph, ili_map:Graph, lexicon_id="own-pt"):
        super().__init__(own_pt)
        self.ili = ili_map
        self.ili.bind("owl", OWL)
        self.lexicon_id = lexicon_id
        self.namespace = {"dc":"https://globalwordnet.github.io/schemas/dc/"}
        
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

        # sense
        # antonym|also|participle|pertainym|derivation|domain_topic|has_domain_topic|domain_region|has_domain_region|exemplifies|is_exemplified_by|similar|other|simple_aspect_ip|secondary_aspect_ip|simple_aspect_pi|secondary_aspect_pi|feminine|has_feminine|masculine|has_masculine|young|has_young|diminutive|has_diminutive|augmentative|has_augmentative|anto_gradable|anto_simple|anto_converse
        self.sense_pointers = {
            SCHEMA.antonymOf:"antonym",
            SCHEMA.seeAlso:"also",
            SCHEMA.participleOf:"participle",
            SCHEMA.adjectivePertainsTo:"pertainym",
            SCHEMA.adverbPertainsTo :"pertainym",
            SCHEMA.derivationallyRelated:"derivation",
            SCHEMA.classifiesByRegion:"domain_region",
            SCHEMA.classifiedByRegion:"has_domain_region",
            SCHEMA.classifiedByTopic:"domain_topic",
            SCHEMA.classifiesByTopic:"has_domain_topic",
            SCHEMA.classifiesByUsage:"exemplifies",
            SCHEMA.classifiedByUsage:"is_exemplified_by",

            SCHEMA.sameVerbGroupAs:"other",

            NOMLEX.agent:"other", 
            NOMLEX.bodyPart:"other", 
            NOMLEX.byMeansOf:"other", 
            NOMLEX.destination:"other", 
            NOMLEX.event:"other", 
            NOMLEX.instrument:"other", 
            NOMLEX.location:"other", 
            NOMLEX.material:"other", 
            NOMLEX.property:"other", 
            NOMLEX.result:"other", 
            NOMLEX.state:"other", 
            NOMLEX.undergoer:"other", 
            NOMLEX.uses:"other", 
            NOMLEX.vehicle:"other",
        }
        
        # synset
        # agent|also|attribute|be_in_state|causes|classified_by|classifies|co_agent_instrument|co_agent_patient|co_agent_result|co_instrument_agent|co_instrument_patient|co_instrument_result|co_patient_agent|co_patient_instrument|co_result_agent|co_result_instrument|co_role|direction|domain_region|domain_topic|exemplifies|entails|eq_synonym|has_domain_region|has_domain_topic|is_exemplified_by|holo_location|holo_member|holo_part|holo_portion|holo_substance|holonym|hypernym|hyponym|in_manner|instance_hypernym|instance_hyponym|instrument|involved|involved_agent|involved_direction|involved_instrument|involved_location|involved_patient|involved_result|involved_source_direction|involved_target_direction|is_caused_by|is_entailed_by|location|manner_of|mero_location|mero_member|mero_part|mero_portion|mero_substance|meronym|similar|other|patient|restricted_by|restricts|result|role|source_direction|state_of|target_direction|subevent|is_subevent_of|antonym|feminine|has_feminine|masculine|has_masculine|young|has_young|diminutive|has_diminutive|augmentative|has_augmentative|anto_gradable|anto_simple|anto_converse|ir_synonym
        self.synset_pointers = {
            SCHEMA.hypernymOf:"hypernym",
            SCHEMA.hyponymOf:"hyponym",
            SCHEMA.hasInstance:"instance_hypernym",
            SCHEMA.instanceOf:"instance_hyponym",
            SCHEMA.entails:"entails",
            SCHEMA.causes:"causes",
            SCHEMA.similarTo:"similar",
            SCHEMA.attribute:"attribute",
            SCHEMA.classifiesByRegion :"domain_region",
            SCHEMA.classifiedByRegion:"has_domain_region",
            SCHEMA.classifiedByTopic:"domain_topic",
            SCHEMA.classifiesByTopic:"has_domain_topic",
            SCHEMA.classifiesByUsage:"exemplifies",
            SCHEMA.classifiedByUsage:"is_exemplified_by",

            SCHEMA.partHolonymOf:"other",
            SCHEMA.partMeronymOf:"other",
            SCHEMA.memberHolonymOf:"other",
            SCHEMA.memberMeronymOf:"other",
            SCHEMA.substanceHolonymOf:"other",
            SCHEMA.substanceMeronymOf:"other",
            SCHEMA.sameVerbGroupAs:"other",
        }

        
    def format(self):
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

        lexicon = Element(
            "Lexicon",
            id=self.lexicon_id,
            url="http://openwordnet-pt.org/",
            label="OpenWordnet-PT",
            email="alexrad@br.ibm.com",
            language="pt",
            license="http://creativecommons.org/licenses/by/4.0/",
            version="21.06", # stands for jun/2021
            citation="http://arademaker.github.io/bibliography/coling2012.html",
            # logo=""
            # dc:publisher="",
            # status="unchecked",
            # confidenceScore=1,
        )

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
        relations = self.get_synset_relations(synset)
        for _, rel, target in relations:
            # adds only if relation only if target has members
            if self.get_synset_members(target) == "": continue

            self.statistics["synset relations"] += 1
            synset_lmf.append(self.get_synset_relation_lmf(rel, target))

        # list of examples for that synset
        examples = self.graph.objects(synset, SCHEMA.example)
        for example in examples:
            self.statistics["synset examples"] += 1
            example_lmf = Element("Example")
            example_lmf.text = example.toPython()
            synset_lmf.append(example_lmf)

        # return synset
        return synset_lmf


    def get_synset_relations(self, synset):
        relations = []
        for pointer in self.synset_pointers:
            relations += list(self.graph.triples((synset, pointer, None)))

        return relations


    def get_synset_members(self, synset):
        members = self.graph.objects(synset, SCHEMA.containsWordSense)
        members_ids = [self._get_sense_id(member) for member in members]
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
        sense_id = self._get_sense_id(sense)
        synset = self.graph.value(predicate=SCHEMA.containsWordSense, object=sense)
        synset_id = self._get_synset_id(synset)
        sense_lmf = Element("Sense", id=sense_id, synset=synset_id)

        # list of relations for that sense
        relations = self.get_sense_relations(sense)
        for _, rel, target in relations:
            self.statistics["sense relations"] += 1
            sense_lmf.append(self.get_sense_relation_lmf(rel, target))
        
        return sense_lmf
    

    def get_sense_relations(self, sense):
        relations = []
        for pointer in self.sense_pointers:
            relations += list(self.graph.triples((sense, pointer, None)))

        return relations
    

    def get_synset_relation_lmf(self, relation, target):
        rel_type = self.synset_pointers[relation]
        return self._get_relation_lmf("SynsetRelation", target, rel_type, str(relation))
 

    def get_sense_relation_lmf(self, relation, target):
        rel_type = self.sense_pointers[relation]
        return self._get_relation_lmf("SenseRelation", target, rel_type, str(relation))
 

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
        

    def _get_sense_id(self, sense):
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