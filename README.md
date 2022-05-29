# TinySearchEngine
A tiny search engine of Wikipedia.

## Usage
(from https://github.com/DhavalTaunk08/Wiki-Search-Engine)

**Data preprocessing**

Download `enwiki-latest-categorylinks.sql.gz` and `enwiki-latest-page.sql.gz` from [this link](https://dumps.wikimedia.org/enwiki/latest/), and load them into the SQL server. Update your SQL configuration in `tree/mysql_config.json`.

*Construct category tree structure*

~~~shell
python ./tree/parse_tree.py --index-folder=/folder/to/save/results
~~~

**Index**

```shell
python english_indexer.py path_to_xml_dump
```

**Search**
```shell
python english_search.py --filename queries.txt --num_results 15
```
The fields **--filename** and **--num_results** are optional. By default **--num_results** is initilaized to **10**. And if you don't pass **--filename** parameter, it will prompt you to enter query on command line.

**Web demo**

~~~shell
python server.py
~~~

