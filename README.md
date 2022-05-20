# TinySearchEngine
A tiny search engine of Wikipedia.

## Usage
(from https://github.com/DhavalTaunk08/Wiki-Search-Engine)

**Index**
```shell
python english_indexer.py path_to_xml_dump
```

**Search**
```shell
python english_search.py --filename queries.txt --num_results 15
```
The fields **--filename** and **--num_results** are optional. By default **--num_results** is initilaized to **10**. And if you don't pass **--filename** parameter, it will prompt you to enter query on command line.