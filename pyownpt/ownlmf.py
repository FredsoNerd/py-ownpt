# -*- coding: utf-8 -*-

import tqdm
import uuid

from lxml.etree import Element, tostring

from rdflib.graph import Graph
from rdflib.namespace import OWL
from pyownpt.ownpt import OWNPT, SCHEMA, PWN30, RDF, RDFS

class OWNPT_LMF(OWNPT):
    def __init__(self, own_pt:Graph, pwn:Graph, ili_map:Graph, lexicon_id="own-pt"):
        super().__init__(own_pt)
        self.pwn = pwn
        self.ili = ili_map
        self.ili.bind("owl", OWL)
        self.lexicon_id = lexicon_id
        
        # statistics
        self.statistics = {    
            "senses": 0,
            "synsets": 0,
            "lexical entries": 0,
            "lexical entries pos": 0,
            "sense relations": 0,
            "synset relations": 0,
            "synset definitions": 0,}

        # sense
        # similar|other|simple_aspect_ip|secondary_aspect_ip|simple_aspect_pi|
        # secondary_aspect_pi|feminine|has_feminine|masculine|has_masculine|young|
        # has_young|diminutive|has_diminutive|augmentative|has_augmentative|
        # anto_gradable|anto_simple|anto_converse
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

            SCHEMA.agent:"other", 
            SCHEMA.bodyPart:"other", 
            SCHEMA.byMeansOf:"other", 
            SCHEMA.destination:"other", 
            SCHEMA.event:"other", 
            SCHEMA.instrument:"other", 
            SCHEMA.location:"other", 
            SCHEMA.material:"other", 
            SCHEMA.property:"other", 
            SCHEMA.result:"other", 
            SCHEMA.state:"other", 
            SCHEMA.undergoer:"other", 
            SCHEMA.uses:"other", 
            SCHEMA.vehicle:"other", 
            SCHEMA.sameVerbGroupAs:"other", #"verb_group",
        }
        
        # synset
        self.synset_pointers = {
            SCHEMA.hypernymOf:"hypernym",
            SCHEMA.hyponymOf:"hyponym",
            SCHEMA.hasInstance:"instance_hypernym",
            SCHEMA.instanceOf:"instance_hyponym",
            SCHEMA.entails:"entails",
            SCHEMA.causes:"causes",
            SCHEMA.similarTo:"similar",
            SCHEMA.seeAlso:"also",
            SCHEMA.attribute:"attribute",

            SCHEMA.classifiesByRegion :"domain_region",
            SCHEMA.classifiedByRegion:"has_domain_region",
            SCHEMA.classifiedByTopic:"domain_topic",
            SCHEMA.classifiesByTopic:"has_domain_topic",
            SCHEMA.classifiesByUsage:"exemplifies",
            SCHEMA.classifiedByUsage:"is_exemplified_by",

            SCHEMA.partHolonymOf:"other", # "part_holonym",
            SCHEMA.partMeronymOf:"other", # "part_meronym",
            SCHEMA.memberHolonymOf:"other", # "member_holonym",
            SCHEMA.memberMeronymOf:"other", # "member_meronym",
            SCHEMA.substanceHolonymOf:"other", # "substance_holonym",
            SCHEMA.substanceMeronymOf:"other", # "substance_meronym",
            SCHEMA.sameVerbGroupAs:"other", # "verb_group",
        }

        
    def format(self):
        self.logger.info("start formating lexical resource")
        self.namespace = {"dc":"https://globalwordnet.github.io/schemas/dc/"}
        lexical_resource = Element("LexicalResource", nsmap=self.namespace)
        lexical_resource.append(self.get_lexicon_lmf())

        for statistics, value in self.statistics.items():
            self.logger.info(f"{statistics} formatted: {value}")

        return tostring(lexical_resource, encoding="UTF-8", pretty_print=True, xml_declaration=True,
            doctype="<!DOCTYPE LexicalResource SYSTEM 'http://globalwordnet.github.io/schemas/WN-LMF-1.0.dtd'>").decode()


    def get_lexicon_lmf(self):
        """"""

        self.logger.info(f"start formatting lexicon '{self.lexicon_id}'")
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
        words = self.graph.query("SELECT ?w WHERE { ?w a wn30:Word }")
        for word, in tqdm.tqdm(words):
            self.statistics["lexical entries"] += 1
            senses = self.graph.subjects(SCHEMA.word, word)
            parts_of_speech = [self.get_pos(sense) for sense in senses]
            parts_of_speech = set(parts_of_speech)
            for pos in parts_of_speech:
                self.statistics["lexical entries pos"] += 1
                self.logger.debug(f"formatting lexical entrie '{word.n3()}' with pos '{pos}'")
                lexicon.append(self.get_lexical_entry_lmf(word, pos))
        

        # list of synsets in your wordnet
        self.logger.info(f"formatting synsets")
        synsets = self.graph.query("SELECT ?s WHERE { VALUES ?t { wn30:Synset wn30:AdjectiveSatelliteSynset wn30:AdjectiveSynset wn30:AdverbSynset wn30:NounSynset wn30:VerbSynset } ?s a ?t . }")
        for synset, in tqdm.tqdm(synsets):
            self.logger.debug(f"formatting synset '{synset.n3()}'")
            synset_lmf = self.get_synset_lmf(synset)
            if not synset_lmf.get("members") == "":
                self.statistics["synsets"] += 1
                lexicon.append(synset_lmf)

        return lexicon


    def get_synset_lmf(self, synset):
        """"""

        sid = self._get_synset_id(synset)
        ili = self.get_ili(synset)
        pos = self.get_pos(synset, "synset-")
        members = self.get_synset_members(synset)
        synset_lmf = Element("Synset", id=sid, ili=ili, partOfSpeech=pos, members=members)

        # list of definitions for that synset
        definitions = []
        definitions += list(self.graph.objects(synset, SCHEMA.gloss))
        definitions += list(self.graph.objects(synset, SCHEMA.example))
        definitions = [definition.toPython() for definition in definitions]
        
        if len(definitions) > 0:
            self.statistics["synset definitions"] += 1
            definition = Element("Definition")
            definition.text = "; ".join(definitions)
            synset_lmf.append(definition)

        # list of relations for that synset
        relations = self._get_synset_relations(synset)
        for source, rel, target in relations:
            self.statistics["synset relations"] += 1
            synset_lmf.append(self.get_synset_relation_lmf(source, rel, target))

        # return synset
        return synset_lmf


    def _get_synset_relations(self, synset):
        """"""

        # list relations for that synset
        relations = []
        for pointer in self.synset_pointers:
            for _, _, target in self.graph.triples((synset, pointer, None)):
                if not self.get_synset_members(target) == "":
                    # accepts relatio only if target got members
                    relations.append((synset, pointer, target))
        
        # indirect relation
        en_synset = self.graph.value(predicate=OWL.sameAs, object=synset)

        if en_synset is not None:
            for pointer in self.synset_pointers:
                # checks relation os PWN
                en_relations = self.pwn.triples((en_synset, pointer, None))
                for _, _, en_target in en_relations:
                    pt_target = self.graph.value(en_target, OWL.sameAs)
                    if pt_target is not None:
                        if not self.get_synset_members(pt_target) == "":
                            # accepts relatio only if target got members
                            relations.append((synset, pointer, pt_target))
                    else:
                        self.logger.warning(f"synset {en_synset} from pwn not maped to ownpt")
        else:
            self.logger.warning(f"synset {synset} from ownpt not maped to pwn")

        # returns relations
        return relations
    

    def get_synset_relation_lmf(self, source, relation, target):
        target_id = self._get_synset_id(target)
        rel_type = self.synset_pointers[relation]
        relation_lmf = Element("SynsetRelation", target=target_id, relType=rel_type)
        relation_lmf.attrib["{{{}}}type".format(self.namespace["dc"])] = str(relation)
        return relation_lmf


    def get_synset_members(self, synset):
        members = self.graph.objects(synset, SCHEMA.containsWordSense)
        members = [self._get_sense_id(member) for member in members]
        return " ".join(sorted(members))


    def get_lexical_entry_lmf(self, word, pos):
        """"""

        # id and lemma
        word_id = f"word-{pos}-{str(uuid.uuid1())}"
        lexical_form = self.graph.value(word, SCHEMA.lexicalForm)
        lexical_entry = Element("LexicalEntry", id=word_id)
        lemma = Element("Lemma", writtenForm=lexical_form, partOfSpeech=pos)
        
        lexical_entry.append(lemma)

        # list of senses for that lexical_entry (word)
        senses = self.graph.subjects(SCHEMA.word, word)
        senses = [sense for sense in senses if self.get_pos(sense) == pos]
        for sense in senses:
            self.statistics["senses"] += 1
            lexical_entry.append(self.get_sense_lmf(sense))

        # returs lexical_entry
        return lexical_entry

    
    def get_sense_lmf(self, sense):
        """"""

        # id and synset 
        sense_id = self._get_sense_id(sense)
        synset = self.graph.value(predicate=SCHEMA.containsWordSense, object=sense)
        synset_id = self._get_synset_id(synset)
         
        sense_lmf = Element("Sense", id=sense_id, synset=synset_id)

        # list of examples for that sense
        # examples = self.graph.objects(sense, SCHEMA.example)
        # for example in examples:
        #     self.statistics["sense relations"] += 1
        #     sense_example_lmf = Element("Example")
        #     sense_example_lmf.text = example.toPython()
        #     sense_lmf.append(sense_example_lmf)

        # list of relations for that sense
        relations = self._get_sense_relations(sense)
        for source, rel, target in relations:
            self.statistics["sense relations"] += 1
            sense_lmf.append(self.get_sense_relation_lmf(source, rel, target))
        
        # return sense
        return sense_lmf
    

    def _get_sense_relations(self, sense):
        """"""

        # list relations for that sense
        relations = []
        for pointer in self.sense_pointers:
            relations += list(self.graph.triples((sense, pointer, None)))
        
        # returns relations
        return relations
 

    def get_sense_relation_lmf(self, source, relation, target):
        target_id = self._get_sense_id(target)
        rel_type = self.sense_pointers[relation]
        relation_lmf = Element("SenseRelation", target=target_id, relType=rel_type)
        relation_lmf.attrib["{{{}}}type".format(self.namespace["dc"])] = str(relation)
        return relation_lmf


    def _get_sense_id(self, sense):
        sense_id = sense.split("/")[-1]
        sense_id = f"{self.lexicon_id}-{sense_id}"
        return sense_id


    def _get_synset_id(self, synset):
        synset_id = synset.split("/")[-1]
        synset_id = f"{self.lexicon_id}-{synset_id}"
        return synset_id


    def get_ili(self, synset):
        synset_id = synset.split("synset-")[-1]
        ili = self.ili.value(predicate=OWL.sameAs, object=PWN30[synset_id])
        if ili is None:
            synset_id = synset_id.replace("a", "s")
            ili = self.ili.value(predicate=OWL.sameAs, object=PWN30[synset_id])

        return ili.split("/")[-1]

    
    def get_pos(self, element, separator="wordsense-"):
        return element.split(separator)[-1].split("-")[1]
        