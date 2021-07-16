# Py-OpenWordnetPT (Py-OWNPT)

This package contains a set of usefull features for manipulation, representation and releasing [OpenWordnet-PT](http://wn.mybluemix.net/). Please, be sure you have the current version of the code installed. Any suggestions are welcome!

## Features

Py-OWNPT contains features for managing OWN-PT, besides convertion to [WN-LMF format](https://globalwordnet.github.io/schemas/#xml). The package `pyownpt.cli` contains the folowing commands-line-interfaces: `update`, `statistics`, `to_lmf` and `split`.

## Updating OWN-PT

For updating OWN-PT, consider the following:
```bash
$ python3 -m pyownpt.cli.update openWordnet-PT/data/own-pt-* --wns openWordnet-PT/dump/wn.jsonl --vts openWordnet-PT/dump/votes.jsonl --sgs openWordnet-PT/dump/suggestion-* -l pt -u arademaker vcvpaiva -o own-pt.nt -v
```

## WN-LMF Format

We follow the [WN-LMF-1.1.dtd](https://globalwordnet.github.io/schemas/WN-LMF-1.1.dtd), considering the [ili-mapping](https://github.com/globalwordnet/cili/blob/master/ili-map.ttl). For formatting, just follow:

```bash
$ python3 -m pyownpt.cli.to_lmf openWordnet-PT/data/own-pt-* path/to/ili-map.ttl -li own-pt -lb OpenWordnet-PT -vr 1.0 -lg pt -cs 1.0 --status checked -v
```

For english is similar, just taking care of changing the configurations as needed. Please, check the help message.

Thanks to [Global WordNet Association](http://globalwordnet.org), John McCrae and Francis Bond for the data, under the [licence](https://github.com/globalwordnet/cili/blob/1276aadc073ca89910f0bd0e89a6a68d7afa3b4a/LICENSE).

## Statistics

If needed, one should be able to generate (update) the `statistics.org` file by following:
```bash
$ python3 -m pyownpt.cli.statistics --ownpt openWordnet-PT/data/own-pt-* --ownen openWordnet-PT/data/own-en-* -v
```

## Logical Splitting

OpenWordnet-PT files are distributed splitted into logical pieces, such as `own-**-synsets.ttl` or `own-**-relations.ttl`. For splitting, follow:
```bash
$ python3 -m pyownpt.cli.split openWordnet-PT/data/own-pt-* -l pt -e ttl -o data -v
```

## Development

One may be able to install Py-OWNPT in developer mode, running
```bash
$ pip install -e /path/to/pyownpt
```
It's advised to install it using a python virtual environment.
