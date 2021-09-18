# -*- coding: utf-8 -*-

from tqdm import tqdm
from rdflib.graph import Graph, Literal, URIRef, BNode
from rdflib.namespace import OWL, RDFS, RDF
from pyownpt.ownpt import OWN, SCHEMA

class Repair(OWN):

    def repair(self):
        """"""

        # actions to apply
        repair_actions = [
            self.add_word_types,
            self.remove_blank_words, # words that are blank nodes
            self.remove_void_words, # without lexical form
            self.remove_double_words, # more than one lexical form

            self.add_sense_types,
            self.replace_blank_senses, # senses that are blank nodes
            self.expand_sense_words, # create word by label
            self.add_sense_labels, # create labels by word
            self.add_sense_number, # add sense word number

            self.format_lexicals, # well defined lexical form
            self.replace_word_uris, # grant unique words uri
            
            self.replace_sense_labels, # match labels to words
            self.remove_word_duplicates, # with same lexical form
            self.remove_sense_duplicates, # same label in a synset
            self.remove_desconex_sense_nodes, # without a synset
            self.remove_desconex_word_nodes, # without a sense

            # self.fix_links_to_satelites,
            # self.fix_synset_id_types,
            # self.remove_lemma_property
            ]

        # apply actions 
        for action in repair_actions:
            name = action.__name__
            
            # computes added/removed before action
            before_added_triples = self.added_triples
            before_removed_triples = self.removed_triples
            # run action
            action_cases = action(name)
            # computes added/removed after action
            after_added_triples = self.added_triples
            after_removed_triples = self.removed_triples
            
            # plots info
            self.logger.info(
                f"action '{name}' applied to {action_cases} cases:"
                    f"\n\t{name}:{after_added_triples - before_added_triples} triples added"
                    f"\n\t{name}:{after_removed_triples - before_removed_triples} triples removed")

        # resulting added and removed triples
        self.logger.info(
            f"all {len(repair_actions)} actions applied"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def repair_words(self):
        """"""
        
        # words repairing actions
        actions = [
            self.format_lexicals, # well defined lexical form
            self.replace_word_uris, # grant unique words uri
            self.replace_sense_labels, # match labels to words
            self.remove_word_duplicates, # with same lexical form
            self.remove_sense_duplicates, # same label in a synset
            self.remove_desconex_sense_nodes, # without a synset
            self.remove_desconex_word_nodes, # without a sense
        ]

        # apply repairing actions
        for action in tqdm(actions):
            name = action.__name__
            results = action(name)
            self.logger.debug(f"action '{name}' applied to {results} cases")

        # added and removed triples
        self.logger.info(
            f"all {len(actions)} actions applied"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")

    def sort_senses_instances(self, name=""):
        """"""
        count = 0
        
        for synset in tqdm(list(self.graph.subjects(SCHEMA.containsWordSense))):
            # selecting senses
            senses = self.graph.objects(synset, SCHEMA.containsWordSense)

            # rename senses
            labels = dict()
            for sense in senses:
                label = self.graph.value(sense, RDFS.label)
                self.graph.remove((sense, SCHEMA.wordNumber, None))
                # replaces sense name
                blank_sense = BNode()
                labels[label] = blank_sense
                self._replace_node(sense, blank_sense)

            # ordered senses
            for label in sorted(labels):
                old_sense = labels[label]
                new_sense = self._new_sense(synset, True)
                self._replace_node(old_sense, new_sense)


    def words_unique_pos(self):
        """"""
        
        count = 0
        nomlex_map = {"n":SCHEMA.noun, "v":SCHEMA.verb}

        self.logger.info(f"start formatting Words to unique POS")
        words = self._get_all_words()
        for word, in words:
            count += 1
            # accesses word POS
            senses = list(self.graph.subjects(SCHEMA.word, word))
            word_pos = set([self._get_pos(sense) for sense in senses])

            # adds pos n or v if nomlex
            for nomlex_pos, nomlex_pred in nomlex_map.items():
                if (None, nomlex_pred, word) in self.graph:
                    word_pos.add(nomlex_pos)

            # splits word given its POS
            for pos in word_pos:
                self.logger.debug(f"format word '{word.n3()}' with pos '{pos}'")
                new_word = URIRef(f"{word.toPython()}-{pos}")

                # copy predications
                self._copy_subject(word, new_word, "copy_word")

                # replace suitable senses
                senses_pos = [s for s in senses if self._get_pos(s) == pos]
                for sense in senses_pos:
                    self._add_triple((sense, SCHEMA.word, new_word), "copy_senses")

                # copies nomlex predications
                for nomlex_pos, nomlex_pred in nomlex_map.items():
                    if nomlex_pos == pos:
                        for subject in self.graph.subjects(nomlex_pred, word):
                            self._add_triple((subject, nomlex_pred, new_word))

                # add property pos
                self._add_triple((new_word, SCHEMA.pos, Literal(pos)), "property_pos")

            # after splitting drops old word
            self._drop_node(word, "drop_word")

        # resulting added and removed triples
        self.logger.info(
            f"action applied to {count} words"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def format_synset_id(self):
        """"""

        count = 0

        self.logger.info(f"start formatting property synsetId")
        synsets = self._get_all_synsets()
        for synset, in synsets:
            count += 1
            
            # removes old property
            synset_id = self.graph.value(synset, SCHEMA.synsetId)
            if synset_id: 
                self._drop_triple((synset, SCHEMA.synsetId, synset_id))

            # replaces property
            synset_id = Literal(synset.split("/synset-")[-1])
            synset_offset = Literal(synset_id.split("-")[0])
            self._add_triple((synset, SCHEMA.offset, synset_offset))
            self._add_triple((synset, SCHEMA.synsetId, synset_id))

        # resulting added and removed triples
        self.logger.info(
            f"action applied to {count} cases"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def format_adjective_satelites(self):
        """"""

        count = 0

        self.logger.info(f"start formatting AdjectiveSatelliteSynset")
        satellite_synsets = self.graph.subjects(RDF.type, SCHEMA.AdjectiveSatelliteSynset)
        for synset in satellite_synsets:
            if synset.endswith("-a"):
                count += 1
                new_synset = URIRef(synset.replace("-a", "-s"))
                self.logger.debug(f"replacing '{synset.n3()}' by '{new_synset.n3()}'")
                self._replace_node(synset, new_synset, "format_adjective_satelites")
                # replace synset id
                synset_id = synset.split("synset-")[-1]
                new_synset_id = new_synset.split("synset-")[-1]
                self._drop_triple((new_synset, SCHEMA.synsetId, Literal(synset_id)), "format_adjective_satelites")
                self._add_triple((new_synset, SCHEMA.synsetId, Literal(new_synset_id)), "format_adjective_satelites")
            else:
                self.logger.warning(f"ill formed AdjectiveSatelliteSynset '{synset.n3()}'")

        # resulting added and removed triples
        self.logger.info(
            f"action applied to {count} valid synsets"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def format_adjective_satelites_sameas(self, ownen:Graph, sameas:Graph):
        """"""

        count = 0

        self.logger.info(f"start formatting AdjectiveSatelliteSynset")
        satellite_synsets = ownen.subjects(RDF.type, SCHEMA.AdjectiveSatelliteSynset)
        for synset_en in satellite_synsets:
            synset_pt = sameas.value(synset_en, OWL.sameAs) 
            if synset_pt is not None:
                count += 1
                self.logger.debug(f"replacing '{synset_pt.n3()}' type by '{SCHEMA.AdjectiveSatelliteSynset.n3()}'")
                self._drop_triple((synset_pt, RDF.type, SCHEMA.AdjectiveSynset), "adjective_satelites")
                self._add_triple((synset_pt, RDF.type, SCHEMA.AdjectiveSatelliteSynset), "adjective_satelites")
            else:
                self.logger.warning(f"counln't find synset_pt sameAs '{synset_en.n3()}'")

        # resulting added and removed triples
        self.logger.info(
            f"action applied to {count} synsets"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {self.removed_triples} triples removed")


    def add_morpho_exceptions(self, exceptions_pos:dict):
        """"""
        
        count = 0
        processed = 0
        not_processed = 0
        for pos, exceptions in exceptions_pos.items():
            self.logger.info(f"processing {len(exceptions)} exceptions with pos '{pos}'")
            # add exceptions
            for form, *lemmas in exceptions:
                for lemma in lemmas:
                    count += 1
                    self.logger.debug(f"processing exception:{pos}: {form} {lemma} ")
                    # attemps finding suitable word
                    word = self._get_word(lemma, pos=pos)
                    if word is not None:
                        processed += 1
                        form = self._new_lexical_literal(form)
                        self._add_triple((word, SCHEMA.exceptionalForm, form), "add_exceptions")
                    else:
                        not_processed += 1
                        self.logger.warning(f"could not process exception:{pos}: {form} {lemma}")
            
        # print statistics
        # resulting added and removed triples
        self.logger.info(
            f"action applied to {count} cases"
                f"\n\ttotal: {self.added_triples} triples added"
                f"\n\ttotal: {processed} exceptions processed"
                f"\n\ttotal: {not_processed} exceptions not processed")
        self.logger.info(f"after action, {self.added_triples} triples were added")


    def add_adjective_markers(self, senses:Graph, adjective_lines):
        """"""
        
        self.logger.info(f"start processing {len(adjective_lines)} lines")

        # format data
        adjective_data = []
        for line in adjective_lines:
            synset_id, _, _, words_count, *tail = line.split()
            for i in range(int(words_count, base=16)):
                adjective_data.append((synset_id, tail[2*i]))
        
        # find and add adjective markers
        count = 0
        for synset_id, word in adjective_data:
            marker = None
            if word.endswith("(a)"): marker = "a" # predicate position
            elif word.endswith("(p)"): marker = "p" # prenominal (attributive) position
            elif word.endswith("(ip)"): marker = "ip" # immediately postnominal position
            else:
                continue
            
            # adds marker
            valid = False
            word = self._format_lexical(word[:word.find(f"({marker})")], True)
            for synset in self.graph.subjects(SCHEMA.synsetId, Literal(synset_id)):
                sense = self._get_sense(synset, word)
                if sense is not None:
                    valid = True
                    count += 1
                    self.logger.debug(f"adding marker '{marker}' from word '{word}' to sense '{sense.n3()}'")
                    senses.add((sense, SCHEMA.adjPosition, Literal(marker)))
            # validates the result
            if not valid:    
                self.logger.warning(f"could not add marker '{marker}' from word '{word}' to synset '{synset_id}'")

        # print statistics
        self.logger.info(f"after action {count} triples were added")


    def remove_lemma_property(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?p ?o WHERE { VALUES ?p { owns:lemma } ?s ?p ?o . }"
        result = self.graph.query(query)

        for triple in result:
            count += 1
            self._drop_triple(triple)

        # how many actions
        return count


    def fix_synset_id_types(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE { VALUES ?t { owns:Synset owns:AdjectiveSatelliteSynset owns:AdjectiveSynset owns:AdverbSynset owns:NounSynset owns:VerbSynset } ?s a ?t . }"
        result = self.graph.query(query)

        for synset, in result:
            synset_id = synset.split("/synset-")[-1].split("-")[0]
            new_synset_id = Literal(synset_id)
            old_synset_id = self.graph.value(synset, SCHEMA.synsetId)
            if not old_synset_id == new_synset_id:
                count += 1
                if old_synset_id is not None:
                    self._drop_triple((synset, SCHEMA.synsetId, old_synset_id), name)
                self._add_triple((synset, SCHEMA.synsetId, new_synset_id), name)

        # how many actions
        return count


    def fix_links_to_satelites(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s2 WHERE { VALUES ?p { owns:adverbPertainsTo owns:derivationallyRelated owns:classifiesByUsage owns:classifiesByTopic owns:classifiesByRegion } ?s1 ?p ?s2 . ?s1 a owns:WordSense . FILTER NOT EXISTS { ?s2 a ?t . } }"
        result = self.graph.query(query)

        for sense, in result:
            new_sense = URIRef(sense.replace("-a-", "-s-"))
            if sense == new_sense:
                continue
            if ((new_sense, RDF.type, SCHEMA.WordSense)) in self.graph:
                count += 1
                self._replace_node(sense, new_sense, name)
            else:
                self.logger.warning(f"sense {sense.n3()} not replaced by {new_sense.n3()}: undefined new sense")

        # how many actions
        return count

        
    def replace_word_uris(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w ?l ?p WHERE { ?w rdf:type owns:Word . ?w owns:lemma ?l . ?w owns:pos ?p }"
        result = self.graph.query(query)
        
        for word, lexical, pos in result:
            new_word = self._new_word(lexical, True, pos)
            if not new_word == word:
                count += 1
                self._replace_node(word, new_word, name)

        # how many actions
        return count


    def remove_desconex_word_nodes(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w WHERE{ ?w rdf:type owns:Word . FILTER NOT EXISTS { ?s ?p ?w . } } "
        result = self.graph.query(query)
        
        for word, in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def remove_desconex_sense_nodes(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE{ ?s rdf:type owns:WordSense . FILTER NOT EXISTS { ?ss owns:containsWordSense ?s . } } "
        result = self.graph.query(query)
        
        for sense, in result:
            count += 1
            self._drop_node(sense, name)

        # how many actions
        return count


    def remove_sense_duplicates(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s2 WHERE{ ?ss owns:containsWordSense ?s1; owns:containsWordSense ?s2 . ?s1 rdfs:label ?l . ?s2 rdfs:label ?l . FILTER ( STR(?s1) < STR(?s2) ) }"
        result = self.graph.query(query)
        
        for sense2, in result:
            count += 1
            self._drop_node(sense2, name)

        # how many actions
        return count


    def remove_word_duplicates(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w1 ?w2 WHERE{ ?w1 owns:lemma ?l . ?w2 owns:lemma ?l . ?w1 owns:pos ?p . ?w2 owns:pos ?p . FILTER ( STR(?w1) < STR(?w2) )}"
        result = self.graph.query(query)
        for word1, word2 in result:
            count += 1
            self._replace_node(word2, word1, name)

        # how many actions
        return count


    def remove_double_words(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?w WHERE{ ?w owns:lemma ?l1 . ?w owns:lemma ?l2 . FILTER ( ?l1 != ?l2 ) }"
        result = self.graph.query(query)

        for word, in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def format_lexicals(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?p ?o WHERE{ VALUES ?p { rdfs:label owns:lemma owns:gloss owns:example owns:lemma } ?s ?p ?o . }"
        result = self.graph.query(query)
        
        for s, p, lexical in result:
            new_lexical = self._format_lexical(lexical.toPython(), True)
            new_lexical = self._new_lexical_literal(new_lexical, True)
            if not new_lexical == lexical:
                count += 1
                self._drop_triple((s, p, lexical), name)
                self._add_triple((s, p, new_lexical), name)

        # how many actions
        return count


    def add_word_types(self, name=""):
        """"""
        count = 0

        query = "SELECT ?w WHERE{ { ?s owns:word ?w } UNION { ?w owns:lemma ?l } . FILTER NOT EXISTS { ?w rdf:type ?t .} }"
        result = self.graph.query(query)
        
        for word, in result:
            count += 1
            self._add_triple((word, RDF.type, SCHEMA.Word), name)

        # how many actions
        return count


    def add_sense_types(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE{ { ?ss owns:containsWordSense ?s . } UNION { ?s owns:word ?w } FILTER NOT EXISTS { ?s rdf:type ?t .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            count += 1
            self._add_triple((sense, RDF.type, SCHEMA.WordSense), name)

        # how many actions
        return count


    def replace_sense_labels(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?sl ?wl WHERE{ ?s rdfs:label ?sl . ?s owns:word ?w . ?w owns:lemma ?wl . FILTER ( ?sl != ?wl )}"
        result = self.graph.query(query)
        
        for sense, label, lexical in result:
            count += 1
            self._drop_triple((sense, RDFS.label, label), name)
            self._add_triple((sense, RDFS.label, lexical), name)

        # how many actions
        return count

    def add_sense_number(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s WHERE{ ?ss owns:containsWordSense ?s . FILTER NOT EXISTS { ?s owns:wordNumber ?n .} }"
        result = self.graph.query(query)
        
        for sense, in result:
            count += 1
            word_number = sense.split("-")[-1]
            word_number = Literal(word_number)
            self._add_triple((sense, SCHEMA.wordNumber, word_number), name)

        # how many actions
        return count



    def add_sense_labels(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?l WHERE{ ?s rdf:type owns:WordSense . ?s owns:word ?w . ?w owns:lemma ?l . FILTER NOT EXISTS { ?s rdfs:label ?l .} }"
        result = self.graph.query(query)
        
        for sense, label in result:
            count += 1
            label = self._new_lexical_literal(label.toPython(), False)
            self._add_triple((sense, RDFS.label, label), name)

        # how many actions
        return count


    def expand_sense_words(self, name=""):
        """"""
        count = 0

        query = "SELECT ?s ?l WHERE{ ?s rdf:type owns:WordSense . ?s rdfs:label ?l . FILTER NOT EXISTS { ?s owns:word ?w . } }"
        result = self.graph.query(query)
        
        for sense, label in result:
            count += 1
            lexical = label.toPython()
            word = self._get_word(lexical, True)
            self._add_triple((sense, SCHEMA.word, word), name)

        # how many actions
        return count


    def remove_void_words(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?w WHERE{ ?w rdf:type owns:Word . FILTER NOT EXISTS { ?w owns:lemma ?l .} }"
        result = self.graph.query(query)
        
        for word in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def remove_blank_words(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?w WHERE { ?w rdf:type owns:Word . FILTER ( isBlank(?w) ) }"
        result = self.graph.query(query)

        for word, in result:
            count += 1
            self._drop_node(word, name)

        # how many actions
        return count


    def replace_blank_senses(self, name=""):
        """"""
        count = 0
        
        query = "SELECT ?ss ?s WHERE { ?ss owns:containsWordSense ?s . FILTER ( isBlank(?s) ) }"
        result = self.graph.query(query)

        for synset, sense in result:
            count += 1
            new_sense = self._new_sense(synset, False)
            self._replace_node(sense, new_sense, name)

        # how many actions
        return count
