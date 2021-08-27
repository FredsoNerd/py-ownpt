# updating OpenWordnet-PT
python3 -m pyownpt.cli.update data/own-pt-* --wns dump/wn.jsonl --vts dump/votes.jsonl --sgs dump/suggestion-* -l pt -u arademaker vcvpaiva -o own-pt.nt -v
python3 -m pyownpt.cli.split own-pt.nt -l pt -e ttl -o data -v

# generating satistics.org
python3 -m pyownpt.cli.statistics --ownpt data/own-pt-* --ownen data/own-en-* -v

# generating LMFs
wget https://raw.githubusercontent.com/globalwordnet/cili/master/ili-map.ttl
python3 -m pyownpt.cli.to_lmf data/own-pt-* ili-map.ttl -li own-pt -lb OpenWordnet-PT -vr 1.0 -lg pt -cs 1.0 --status checked -o own-pt-lmf-10.xml -v
python3 -m pyownpt.cli.to_lmf data/own-en-* ili-map.ttl -li own-en -lb OpenWordnet-EN -vr 1.0 -lg en -cs 1.0 --status checked -o own-en-lmf-10.xml -v

# remove files
rm ili-map.ttl own-pt.nt log-update log-format
