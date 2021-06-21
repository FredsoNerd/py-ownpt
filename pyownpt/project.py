# -*- coding: utf-8 -*-

from pyownpt.ownpt import OWNPT, SCHEMA, NOMLEX, OWL, Graph

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

        # apply actions 
        for pointer in self.pwn_pointers:
            name = pointer.n3()
            
            before_added_triples = self.added_triples
            self.project_relation(pointer)
            after_added_triples = self.added_triples
            
            # plots info
            self.logger.info(f"pointer '{name} : {after_added_triples - before_added_triples} triples added")

        # resulting added and removed triples
        self.logger.info(f"all {len(self.pwn_pointers)} pointers projected")
        self.logger.info(f"Total: {self.added_triples} triples added")
        self.logger.info(f"Total: {self.counter} triples checked")

    
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