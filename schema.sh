# prefix schema: rename wn30 to owns
sed -i "s#wn30:#owns:#g" data/*
sed -i "s#https://w3id.org/own-pt/wn30/schema/#https://w3id.org/own/schema/#g" data/*

# prefix instances
sed -i "s#https://w3id.org/own-pt/wn30-pt/instances/#https://w3id.org/own/own-pt/instances/#g" data/*
sed -i "s#https://w3id.org/own-pt/wn30-en/instances/#https://w3id.org/own/own-en/instances/#g" data/*

# predicates skos:inScheme
sed -i "s#http://logics.emap.fgv.br/wn/#https://w3id.org/own/own-pt/instances/#g" data/own-pt-synsets.ttl
sed -i "s#http://logics.emap.fgv.br/wn/#https://w3id.org/own/own-en/instances/#g" data/own-en-synsets.ttl

# review nomlex URIs
sed -i "s#nomlex:#owns:#g" data/own-*-morphosemantic-links.ttl
sed -i "s#https://w3id.org/own-pt/nomlex/schema/#https://w3id.org/own/schema/#g" data/own-*-morphosemantic-links.ttl

sed -i "s#https://w3id.org/own-pt/nomlex/instances/#https://w3id.org/own/own-pt/instances/#g" data/own-pt-morphosemantic-links.ttl
sed -i "s#https://w3id.org/own-pt/nomlex/instances/#https://w3id.org/own/own-en/instances/#g" data/own-en-morphosemantic-links.ttl

# update serialization
python3 -m pyownpt.cli.split data/own-pt-* -l pt -e ttl -o data -v
python3 -m pyownpt.cli.split data/own-en-* -l en -e ttl -o data -v

rm data/own-en-same-as.ttl