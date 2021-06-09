# Py-OpenWordnetPT (Py-OWNPT)

This package contains a set of usefull features for manipulation, representation and releasing [OpenWordnet-PT](http://wn.mybluemix.net/).

## Features

Py-OWNPT contains features for `repair`, `compare` and `update` OWN-PT. The directoy `pwownpt/cli` contains the folowing commands: `repair_ownpt`, `compare_dump_ownpt` and `update_ownpt`.

## Updating OWN-PT

For repairing and updating of OWN-PT, consider the following steps; if any doubts try the help flag `-h`:

 - Be sure you have the current version of the code installed;

 - Repair the current own-pt files. This attemps to grant a well formed wordnet:

```bash
$ python path/to/repair_ownpt.py path/to/own-pt.nt -o own-pt-repaired.nt -v
```

 - Compare the result `own-pt-repaired.nt` and the current dump `wn.json`. This is going to generate an output `compare.json` containing the differences between documents, and actions for unification. If you need to compare includding morphosemantic-links, add a `-m` flag:

```bash
$ python path/to/compare_dump_ownpt.py own-pt-repaired.nt path/to/wn.json -m -o compare.json -v
```

 - Finally, update the wordnet considering votes and suggestions. Add a `-a` flag for parsing previous output `compare.json` containing actions for unification, wich are applied before suggestions. In the following example, *arademaker* and *vcvpaiva* are the senior users responsible for the project:

```bash
$ python path/to/update_ownpt.py own-pt-repaired.nt path/to/suggestions.json path/to/votes.json -u arademaker vcvpaiva -a compare.json -o own-pt-updated.nt -v
```

After those steps, is advertisable to repair the updated file once more, adding types and removing desconex nodes.

## Repair OWN-PT (english)

For repairing OWN-PT (english), we use similar step as before:

```bash
$ python path/to/repair_ownpt.py path/to/own-en-morpho.nt -e -o own-en-morpho-repaired.nt -v
```

The `-e` flag configures the environment to english specific resources.

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
