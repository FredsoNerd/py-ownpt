# -*- coding: utf-8 -*-

from re import sub
from io import StringIO
from logging import getLogger
from lxml.etree import Element, DTD
from html.entities import html5, entitydefs
from rdflib import Graph, Namespace, Literal, SKOS, DC, RDF, RDFS, OWL

# global
PWN30 = Namespace("http://wordnet-rdf.princeton.edu/wn30/")

SCHEMA = Namespace("https://w3id.org/own-pt/wn30/schema/")
NOMLEX = Namespace("https://w3id.org/own-pt/nomlex/schema/")

WORD = Namespace("https://w3id.org/own-pt/wn30-pt/instances/word-")
SYNSET = Namespace("https://w3id.org/own-pt/wn30-pt/instances/synset-")
WORDSENSE = Namespace("https://w3id.org/own-pt/wn30-pt/instances/wordsense-")

WORD_EN = Namespace("https://w3id.org/own-pt/wn30-en/instances/word-")
SYNSET_EN = Namespace("https://w3id.org/own-pt/wn30-en/instances/synset-")
WORDSENSE_EN = Namespace("https://w3id.org/own-pt/wn30-en/instances/wordsense-")


class OWNPT():
    def __init__(self, graph:Graph, lang="pt"):
        self.lang = lang
        self.graph = graph
        self.graph.bind("dc", DC)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("skos", SKOS)
        self.graph.bind("wn30", SCHEMA)
        self.graph.bind("pwn30", PWN30)
        self.graph.bind("nomlex", NOMLEX)

        # define local schema
        if self.lang == "pt":
            self.WORD = WORD
            self.SYNSET = SYNSET
            self.WORDSENSE = WORDSENSE 
        if self.lang == "en":
            self.WORD = WORD_EN
            self.SYNSET = SYNSET_EN
            self.WORDSENSE = WORDSENSE_EN 

        # statistics
        self.added_triples = 0
        self.removed_triples = 0

        # pointers
        self.pointers = {
            SCHEMA.antonymOf:"antonym",
            SCHEMA.seeAlso:"also",
            SCHEMA.participleOf:"participle",
            SCHEMA.adjectivePertainsTo:"pertainym",
            SCHEMA.adverbPertainsTo:"derivation",
            SCHEMA.derivationallyRelated:"derivation",
            SCHEMA.classifiesByRegion:"has_domain_region",
            SCHEMA.classifiedByRegion:"domain_region",
            SCHEMA.classifiesByTopic:"has_domain_topic",
            SCHEMA.classifiedByTopic:"domain_topic",
            SCHEMA.classifiesByUsage:"is_exemplified_by",
            SCHEMA.classifiedByUsage:"exemplifies",
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

            NOMLEX.agent: "other", # "agent"
            NOMLEX.bodyPart:"other", 
            NOMLEX.byMeansOf:"other", 
            NOMLEX.destination:"other", 
            NOMLEX.event:"other", 
            NOMLEX.instrument: "other", # "instrument"
            NOMLEX.location: "other", # "location"
            NOMLEX.material:"other", 
            NOMLEX.property:"other", 
            NOMLEX.result: "other", # "result"
            NOMLEX.state:"other", 
            NOMLEX.undergoer:"other", 
            NOMLEX.uses:"other", 
            NOMLEX.vehicle:"other",
        }

        # unicode mapping
        self.unicode_entity_names = dict()
        for name in sorted(html5, reverse=True):
            char = html5[name]
            name = name.strip(";").strip("&")
            self.unicode_entity_names[char] = name

        # synset types
        self.synset_types = [
            SCHEMA.Synset, 
            SCHEMA.VerbSynset, 
            SCHEMA.NounSynset,
            SCHEMA.AdverbSynset, 
            SCHEMA.AdjectiveSynset,
            SCHEMA.AdjectiveSatelliteSynset]
        # sense types
        self.sense_types = [
            SCHEMA.WordSense, 
            SCHEMA.NounWordSense, 
            SCHEMA.VerbWordSense,
            SCHEMA.AdverbWordSense,
            SCHEMA.AdjectiveWordSense, 
            SCHEMA.AdjectiveSatelliteWordSense]

        # logging
        self.logger = getLogger("ownpt")


    def _new_sense(self, synset, add_sense=False):
        """"""
        # synset_id from uri
        synset_id = synset.split("/")[-1]
        synset_id = synset_id[synset_id.find("-")+1:]

        _WORDSENSE = None
        if self.lang == "pt": _WORDSENSE = WORDSENSE
        if self.lang == "en": _WORDSENSE = WORDSENSE_EN 
        # finds new sense_id 
        sense_id = 1
        while True:
            # new sense to add
            new_sense = _WORDSENSE[f"{synset_id}-{sense_id}"]
            new_triple = (synset, SCHEMA.containsWordSense, new_sense)

            # validate new sense
            if new_triple not in self.graph:
                break
            
            # update counter
            sense_id += 1

        # connect sense
        if add_sense:
            self._add_triple((new_sense, RDF.type, SCHEMA.WordSense))
            self._add_triple((synset, SCHEMA.containsWordSense, new_sense))
            self._add_triple((new_sense, SCHEMA.wordNumber, Literal(str(sense_id))))

        return new_sense


    def _get_sense(self, synset, lexical:str):
        """"""

        lexical = self._format_lexical(lexical)
        for sense in self.graph.objects(synset, SCHEMA.containsWordSense):
            label = self.graph.value(sense, RDFS.label)
            if label is not None:
                label = self._format_lexical(label)
                if label == lexical:
                    return sense
        
        return None


    def _word_uri_by_blank(self, sense, word):
        """"""

        # if word has lexical form
        lexical_form = self.graph.value(word, SCHEMA.lexicalForm)
        if lexical_form is not None:
            lexical_form = lexical_form.toPython()
            return self._new_word(lexical_form)

        # otherwise
        sense_label = self.graph.value(sense, RDFS.label)
        lexical = sense_label.toPython()
        return self._get_word(lexical, True)


    def _get_word(self, lexical_form:str, create_new=False, pos=None):
        """"""

        # formats lexical
        lexical_form = Literal(lexical_form, lang=self.lang)
        # checks each word
        words = self.graph.subjects(SCHEMA.lemma, lexical_form)
        for word in words:
            word_pos = self.graph.value(word, SCHEMA.pos)
            if word_pos and word_pos.toPython() == pos: return word
        # if cant find word
        if create_new:
            return self._new_word(lexical_form, True, pos)
        # if resulting words
        return None


    def _new_word(self, lexical:str, add_word=False, pos=None):
        """"""

        # formats word
        word = f"{lexical}-{pos}"
        word = sub(r" ", "_", word)
        word = self._scape_lemma(word)

        # gets suitable preffix
        word = self.WORD[word]

        # defines new word
        if add_word:
            self._add_triple((word, RDF.type, SCHEMA.Word), "new_word")
            self._add_triple((word, SCHEMA.pos, Literal(pos)), "new_word")
            self._add_triple((word, SCHEMA.lemma, Literal(lexical, lang=self.lang)), "new_word")

        return word


    def _replace_node(self, old_node, new_node, prefix="replace"):
        """"""

        self.logger.debug(f"{prefix}:replacing node '{old_node.n3()}' by '{new_node.n3()}'")

        # replaces objects
        result = self.graph.subject_predicates(old_node)
        for s,p in result:
            self._drop_triple((s,p,old_node), prefix)
            self._add_triple((s,p,new_node), prefix)
        
        # replaces subjects
        result = self.graph.predicate_objects(old_node)
        for p, o in result:
            self._drop_triple((old_node,p,o), prefix)
            self._add_triple((new_node,p,o), prefix)


    def _drop_node(self, node, prefix="drop_node"):
        """"""
        
        self.logger.debug(f"{prefix}:dropping node '{node.n3()}'")

        for triple in self.graph.triples((node,None,None)):
            self._drop_triple(triple, prefix)
        for triple in self.graph.triples((None,None,node)):
            self._drop_triple(triple, prefix)


    def _add_triple(self, triple, prefix="add_triple"):
        s,p,o = triple
        
        if triple not in self.graph:
            self.logger.debug(f"{prefix}:adding triple: {s.n3()} {p.n3()} {o.n3()}")
            self.graph.add(triple)

            # count triples added
            self.added_triples += 1

            return True
        
        # if not adding
        self.logger.debug(f"{prefix}:triple already in graph: {s.n3()} {p.n3()} {o.n3()}")
        return False

        
    def _drop_triple(self, triple, prefix="drop_triple"):
        s,p,o = triple

        if triple in self.graph:
            self.logger.debug(f"{prefix}:removing triple: {s.n3()} {p.n3()} {o.n3()}")
            self.graph.remove(triple)
            # count triples removed
            self.removed_triples += 1
            return True
        
        # if not removing
        self.logger.debug(f"{prefix}:triple not in graph: {s.n3()} {p.n3()} {o.n3()}")
        return False

    
    def _copy_subject(self, old_node, new_node, prefix="copy_subject"):
        for predicate, object in self.graph.predicate_objects(old_node):
            self._add_triple((new_node, predicate, object), prefix)

    
    def _new_lexical_literal(self, lexical, format=False):
        if format:
            lexical = self._format_lexical(lexical)
        return Literal(lexical, lang=self.lang)


    def _format_lexical(self, lexical, replace_punctuation=False):
        if replace_punctuation:
            lexical = sub(r"\_", " ", lexical).strip()
        return sub(r"\s+", " ", lexical).strip()


    def _get_gloss(self, synset, lexical_form:str):
        """"""
        
        lexical_form = self._format_lexical(lexical_form)
        for gloss in self.graph.objects(synset, SCHEMA.gloss):
            lexical = gloss.toPython()
            if self._format_lexical(lexical) == lexical_form:
                return gloss
        
        return None

    
    def _get_example(self, synset, lexical_form:str):
        """"""
        
        lexical_form = self._format_lexical(lexical_form)
        for example in self.graph.objects(synset, SCHEMA.example):
            lexical = example.toPython()
            if self._format_lexical(lexical) == lexical_form:
                return example
        
        return None


    def _get_node_id(self, sense):
        return self._get_node_suffix(sense)


    def _get_synset_id(self, synset):
        return self._get_node_suffix(synset)


    def _get_node_suffix(self, node):
        return f"{self.lexicon_id}-{node.split('instances/')[-1]}"

    
    def _get_pos(self, element, separator="wordsense-"):
        ss_type = element.split(separator)[-1].split("-")[1]
        return "a" if ss_type == "s" else ss_type

    
    def _get_all_words(self):
        return self.graph.query("SELECT ?w WHERE { ?w a wn30:Word }")
    
    
    def _get_all_synsets(self):
        return self.graph.query("SELECT ?s WHERE { VALUES ?t { wn30:Synset wn30:AdjectiveSatelliteSynset wn30:AdjectiveSynset wn30:AdverbSynset wn30:NounSynset wn30:VerbSynset } ?s a ?t . }")
        
    
    def _get_synset_by_id(self, synset_id):
        synset = self.graph.value(predicate=SCHEMA.synsetId, object=Literal(synset_id))
        if synset is None and synset_id.endswith("-a"):
            synset_id = synset_id.replace("-a", "-s") # from satellites
        return self.graph.value(predicate=SCHEMA.synsetId, object=Literal(synset_id))

    
    def _scape_lemma(self, lemma:str):
        return "".join(self._scape_char(char) for char in lemma)

    
    def _scape_char(self, char:str):
        if self._validate_dtd_name_char(char):
            return char
        if char in self.unicode_entity_names:
            return f"-{self.unicode_entity_names[char]}-"
        return f"-{char.encode().hex()}-"


    def _validate_dtd_start_char(self, char:str):
        return self._validate_dtd_name(char)
    
    def _validate_dtd_name_char(self, char:str):
        return self._validate_dtd_name("id" + char)

    def _validate_dtd_name(self, identifier:str):
        dtd = "<!ELEMENT S EMPTY><!ATTLIST S id ID #REQUIRED>"
        dtd_file = StringIO(dtd)
        dtd_validator = DTD(dtd_file)
        sample_xml_element = Element("S", id = identifier)
        return dtd_validator.validate(sample_xml_element)
