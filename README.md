# Py-OpenWordnetPT (Py-OWNPT)

This package contains a set of usefull features for manipulation, representation and releasing [OpenWordnet-PT](http://wn.mybluemix.net/).

## Features

Py-OWNPT contains features for `repair`, `compare` and `update` OWN-PT. The directoy `cli` contains the folowing commands: `repair_ownpt`, `compare_dump_ownpt` and `update_ownpt`.

For repairing and updating of OWN-PT, consider the following steps; if any doubts try the help flag `-h`:

 - Be sure you have the current version of the code installed; new features and packages may have been added;

 - Repair the current own-pt files; this attemps to grant a well formed wordnet:

```bash
$ python path/to/repair_ownpt.py path/to/own-pt.nt -o own-pt-repaired.nt -v
```

 - After that, we compare the resulting file `own-pt-repaired.nt` and the current dump; this is going to generate an output `compare.json` containing the differences between documents, and actions for unification:

```bash
$ python path/to/compare_dump_ownpt.py own-pt-repaired.nt path/to/wn.json -o compare.json -v
```

You may want a complete comparing, considering morphosemantic-links, in this case add a `-m` flag: 

```bash
$ python path/to/compare_dump_ownpt.py own-pt-repaired.nt path/to/wn.json -m path/to/morphosemantic-links-pt.nt -o compare.json -v
```

 - Finally, we update the wordnet, considering votes and suggestions; notice we add a `-a` flag, since we're interested in parsing the previous output `compare.json` containing actions to apply. In this example, 'arademaker' and 'vcvpaiva' are the senior users responsible for the project:

```bash
$ python path/to/compare_dump_ownpt.py own-pt-repaired.nt path/to/suggestions.json path/to/votes.json -u arademaker vcvpaiva -a compare.json -o own-pt-updated.nt -v
```

After those steps, is advertisable to repair the updated file once more.

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