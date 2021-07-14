# -*- coding: utf-8 -*-

from rdflib import graph
from pyownpt.ownpt import OWNPT, SCHEMA, NOMLEX, OWL, RDF, Graph

class ProjectRelations(OWNPT):

    def __init__(self, own_pt:Graph, pwn:Graph):
        super().__init__(own_pt)
        self.pwn = pwn

        self.counter = 0

        # pwn pointers
        self.pwn_pointers = [
            SCHEMA.adjectivePertainsTo,
            SCHEMA.adverbPertainsTo,
            SCHEMA.antonymOf,
            SCHEMA.attribute,
            SCHEMA.causes,
            SCHEMA.classifiedByRegion,
            SCHEMA.classifiedByTopic,
            SCHEMA.classifiedByUsage,
            SCHEMA.classifiesByRegion,
            SCHEMA.classifiesByTopic,
            SCHEMA.classifiesByUsage,
            SCHEMA.derivationallyRelated,
            SCHEMA.entails,
            SCHEMA.hasInstance,
            SCHEMA.hypernymOf,
            SCHEMA.hyponymOf,
            SCHEMA.instanceOf,
            SCHEMA.similarTo,
            SCHEMA.substanceHolonymOf,
            SCHEMA.substanceMeronymOf,
            SCHEMA.memberHolonymOf,
            SCHEMA.memberMeronymOf,
            SCHEMA.partHolonymOf,
            SCHEMA.participleOf,
            SCHEMA.partMeronymOf,
            SCHEMA.sameVerbGroupAs,
            SCHEMA.seeAlso,

            NOMLEX.agent,
            NOMLEX.bodyPart,
            NOMLEX.byMeansOf,
            NOMLEX.destination,
            NOMLEX.event,
            NOMLEX.instrument,
            NOMLEX.location,
            NOMLEX.material,
            NOMLEX.property,
            NOMLEX.result,
            NOMLEX.state,
            NOMLEX.undergoer,
            NOMLEX.uses,
            NOMLEX.vehicle,
        ]

    def project(self):
        """"""

        # project relations
        for pointer in self.pwn_pointers:
            name = pointer.n3()
            
            before_added_triples = self.added_triples
            self.project_relation(pointer)
            after_added_triples = self.added_triples
            
            # plots info
            self.logger.info(f"pointer '{name} : {after_added_triples - before_added_triples} triples added")

        # project CoreConcept
        self.project_property(RDF.type, SCHEMA.CoreConcept)
        # project BaseConcept
        self.project_property(RDF.type, SCHEMA.BaseConcept)

        # resulting added and removed triples
        self.logger.info(f"all {len(self.pwn_pointers)} pointers projected"
            f"\n\ttotal: {self.added_triples} triples added"
            f"\n\ttotal: {self.counter} triples checked")

    
    def project_relation(self, pointer, name=""):

        sources_targets_en = self.pwn.subject_objects(pointer)

        for source_en, target_en in sources_targets_en:
            self.counter += 1
            
            source_pt = self.graph.value(source_en, OWL.sameAs)
            target_pt = self.graph.value(target_en, OWL.sameAs)

            if source_pt is not None and target_pt is not None:
                self._add_triple((source_pt, pointer, target_pt), name)
            else:
                self.logger.debug(f"relation '{pointer}' not maped : source '{source_en}':'{source_pt}' and target '{target_en}':'{target_pt}'")


    def project_property(self, predicate, property):
        """"""
        
        self.logger.info(f"start projecting property '{predicate.n3()}' '{property.n3()}'")
        for synset_en in self.pwn.subjects(predicate, property):
            synset_pt = self.graph.value(synset_en, OWL.sameAs)
            
            if synset_pt is not None:
                self._add_triple((synset_pt, predicate, property), "project_property")
                self.logger.debug(f"adding property '{property.n3()}' to '{synset_pt.n3()}'")
            else:
                self.logger.warning(f"could not find synset sameAs '{synset_en.n3()}'")