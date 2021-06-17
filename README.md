# Py-OpenWordnetPT (Py-OWNPT)

This package contains a set of usefull features for manipulation, representation and releasing [OpenWordnet-PT](http://wn.mybluemix.net/).

## Features

Py-OWNPT contains features for repairing, comparing and updating OWN-PT, besides convertion to [WN-LMF format](https://globalwordnet.github.io/schemas/#xml). The directoy `pwownpt/cli` contains the folowing commands: `repair_ownpt`, `compare_dump_ownpt`, `update_ownpt` and `ownlmf_format`.

## Updating OWN-PT

For repairing and updating of OWN-PT, consider the following steps; be sure you have the current version of the code installed:

 - Repair the current own-pt files. This attemps to grant a well formed wordnet;
 - Compare the result `own-pt-repaired.nt` and the current dump `wn.json`. This is going to generate an output `compare.json` containing the differences between documents, and actions for unification. If you need to compare includding morphosemantic-links, add a `-m` flag;
 - Finally, update the wordnet considering votes and suggestions. Add a `-a` flag for parsing previous output `compare.json` containing actions for unification, wich are applied before suggestions. In the following example, *arademaker* and *vcvpaiva* are the senior users responsible for the project;
 - After those steps, is advertisable to repair the updated file once more, adding types and removing desconex nodes:

```bash
$ python path/to/repair_ownpt.py path/to/own-pt.nt -o own-pt-repaired.nt -v
$ python path/to/compare_dump_ownpt.py own-pt-repaired.nt path/to/wn.json -m -o compare.json -v
$ python path/to/update_ownpt.py own-pt-repaired.nt path/to/suggestions.json path/to/votes.json -u arademaker vcvpaiva -a compare.json -o own-pt-updated.nt -v
$ python path/to/repair_ownpt.py own-pt-updated.nt -o own-pt-final.nt -v
```

After those steps, the resulting OWN-PT should `own-pt-final.nt`.

## Repair OWN-PT (english)

For repairing OWN-PT (english), we use similar step as before. The `-e` flag configures the environment to english specific resources:

```bash
$ python path/to/repair_ownpt.py path/to/own-en-morpho.nt -e -o own-en-morpho-repaired.nt -v
```

## WN-LMF Format

We follow the [WN-LMF-1.1.dtd](https://globalwordnet.github.io/schemas/WN-LMF-1.1.dtd), considering the [ili-mapping](https://github.com/globalwordnet/cili/blob/master/ili-map.ttl). For formatting, just follow:

```
$ python oath/to/ownlmf_format.py own-pt-files/own-pt-* ili-map.ttl -v
```

Thanks to [Global WordNet Association](http://globalwordnet.org), John McCrae and Francis Bond for the data, under the [licence](https://github.com/globalwordnet/cili/blob/1276aadc073ca89910f0bd0e89a6a68d7afa3b4a/LICENSE). 

## Development

One may be able to install Py-OWNPT in developer mode, running
```bash
$ pip install -e /path/to/pyownpt
```
Wich allows you to remove the package simply by running
```bash
$ pip uninstall pyownpt
```
It's advised to install it using a python virtual environment.
