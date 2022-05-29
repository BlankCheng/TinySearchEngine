import os
import os.path as osp
import shutil
import argparse
import linecache
import time
import pickle
from tqdm import tqdm

import numpy as np

from tree_utils import backtrack, calc_tree_size, calc_node_num
from mysql_utils import mysql_connect, mysql_fetch_main_topic_id, mysql_fetch_page_title


num_cat = 0
num_file = 0
MAX_LINE = 10000
wikiid_tmpid_map = {}
descendent_buffer = {}  # deprecated
cat_postings_buffer = {}
shortest_paths_buffer = {}


def save_obj(obj, path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_wikiid_title_map(cursor, category_tree, save_folder):
    wikiid_list = sorted(category_tree.keys(), key=lambda wikiid: str(wikiid))
    with open(osp.join(save_folder, "wikiid_title_map.txt"), "w") as f:
        for wikiid in tqdm(wikiid_list):
            title = mysql_fetch_page_title(cursor, wikiid)
            f.write(f"{wikiid}-{title}\n")
    return

class WriteTree(object):
    def __init__(self, save_folder):
        self.save_folder = save_folder

    def write_cat_postings_buffer(self):
        global cat_postings_buffer, num_file, wikiid_tmpid_map
        id_list = sorted(cat_postings_buffer.keys(), key=lambda id: wikiid_tmpid_map[id])
        with open(osp.join(self.save_folder, f"cat_postings_{num_file}.txt"), "w") as f:
            for id in id_list:
                postings = cat_postings_buffer[id]
                f.write(f"{id}-{';'.join([str(item) for item in sorted(postings)])}\n")

    def write_cat_postings_id_info(self):
        global wikiid_tmpid_map, MAX_LINE
        write_data = [(str(wikiid), str(tmpid // MAX_LINE), str(tmpid % MAX_LINE))
                      for wikiid, tmpid in wikiid_tmpid_map.items()]
        write_data = sorted(write_data, key=lambda item: item[0])
        with open(osp.join(self.save_folder, f"cat_postings_id_info.txt"), "w") as f:
            for data in write_data:
                f.write(f"{'-'.join(data)}\n")
        with open(osp.join(self.save_folder, f"cat_postings_nline.txt"), "w") as f:
            f.write(f"{len(write_data)}\n")

    def write_descendent_buffer(self):
        global descendent_buffer, num_file, wikiid_tmpid_map
        id_list = sorted(descendent_buffer.keys(), key=lambda id: wikiid_tmpid_map[id])
        with open(osp.join(self.save_folder, f"descendents_{num_file}.txt"), "w") as f:
            for id in id_list:
                des = descendent_buffer[id]
                f.write(f"{id}-{';'.join([str(item) for item in sorted(des)])}\n")

    def write_descendent_id_info(self):
        global wikiid_tmpid_map, MAX_LINE
        write_data = [(str(wikiid), str(tmpid // MAX_LINE), str(tmpid % MAX_LINE))
                      for wikiid, tmpid in wikiid_tmpid_map.items()]
        write_data = sorted(write_data, key=lambda item: item[0])
        with open(osp.join(self.save_folder, f"descendents_id_info.txt"), "w") as f:
            for data in write_data:
                f.write(f"{'-'.join(data)}\n")
        with open(osp.join(self.save_folder, f"descendents_nline.txt"), "w") as f:
            f.write(f"{len(write_data)}\n")

    def write_shortest_path_buffer(self):
        global shortest_paths_buffer, num_file, wikiid_tmpid_map
        id_list = sorted(shortest_paths_buffer.keys(), key=lambda id: wikiid_tmpid_map[id])
        with open(osp.join(self.save_folder, f"shortest_paths_{num_file}.txt"), "w") as f:
            for id in id_list:
                sp = shortest_paths_buffer[id]
                description = []
                for topic, path in sp.items():
                    if path is None: continue
                    description.append(f"{topic}:" + ";".join([str(node) for node in path]))
                f.write(f"{id}-{'|'.join(description)}\n")

    def write_shortest_path_id_info(self):
        global wikiid_tmpid_map, MAX_LINE
        write_data = [(str(wikiid), str(tmpid // MAX_LINE), str(tmpid % MAX_LINE))
                      for wikiid, tmpid in wikiid_tmpid_map.items()]
        write_data = sorted(write_data, key=lambda item: item[0])
        with open(osp.join(self.save_folder, f"shortest_paths_id_info.txt"), "w") as f:
            for data in write_data:
                f.write(f"{'-'.join(data)}\n")
        with open(osp.join(self.save_folder, f"shortest_paths_nline.txt"), "w") as f:
            f.write(f"{len(write_data)}\n")


class TreeParser(object):
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.write_tree = WriteTree(output_folder)
        self._get_page_id()
        self.category_tree = None

    def _get_page_id(self):
        with open(osp.join(self.input_folder, 'num_pages.txt'), 'r') as f:
            num_pages = int(f.readline().strip())

        self.all_wiki_id = []
        for i in range(1, num_pages + 1):
            line = linecache.getline(osp.join(self.input_folder, "pageid_wikiid_map.txt"), i)
            wiki_id = int(line.split('-', 1)[1])
            self.all_wiki_id.append(wiki_id)

        assert len(self.all_wiki_id) == num_pages
        return self.all_wiki_id

    def get_tree(self, cursor, print_freq=1000):
        category_tree = {}
        t0 = time.time()
        root_ids = mysql_fetch_main_topic_id(cursor)
        for cnt, wiki_id in enumerate(self.all_wiki_id):
            backtrack(cursor, page_id=wiki_id, root_ids=root_ids, category_tree=category_tree)
            if (cnt + 1) % print_freq == 0:
                print(f"Processed {cnt + 1} pages, time elapsed: {time.time() - t0:.2f} seconds. "
                      f"| Tree size (|V|+|E|): {calc_tree_size(category_tree)} "
                      f"| # of non-leaf nodes: {calc_node_num(category_tree)}.")
        print(f"Processed {len(self.all_wiki_id)} pages, time elapsed: {time.time() - t0:.2f} seconds. "
              f"| Tree size (|V|+|E|): {calc_tree_size(category_tree)} "
              f"| # of non-leaf nodes: {calc_node_num(category_tree)}.")
        self.category_tree = category_tree
        self.main_topic_id = root_ids

        num_main_topic = 0
        for id in root_ids:
            if id in category_tree:
                num_main_topic += 1
        print("# of main topics covered:", num_main_topic)

        return self.category_tree

    def save_tree(self, save_name="raw.bin"):
        if self.category_tree is None:
            print("Please initialize the tree by calling 'get_tree'.")
            return
        save_obj(self.category_tree, osp.join(self.output_folder, save_name))

    def prune_tree(self):
        self.is_valid = {}
        for wikiid in self.all_wiki_id:
            self._check_category_validity(wikiid)

        num_valid_category = 0
        for wikiid in self.is_valid:
            if self.is_valid[wikiid]:
                num_valid_category += 1
        print(len(self.is_valid), len(self.category_tree))
        print("# of valid categories:", num_valid_category)

        category_tree_pruned = {}
        for wikiid in self.category_tree:
            if not self.is_valid[wikiid]:
                continue
            category_tree_pruned[wikiid] = []
            for child in self.category_tree[wikiid]:
                if self.is_valid[child]:
                    category_tree_pruned[wikiid].append(child)

        num_main_topic = 0
        for id in self.main_topic_id:
            if id in category_tree_pruned:
                num_main_topic += 1
        print("# of main topics covered (after pruning):", num_main_topic)
        print(f"After pruning: "
              f"Tree size (|V|+|E|): {calc_tree_size(self.category_tree)}->{calc_tree_size(category_tree_pruned)} "
              f"| # non-leaf node: {calc_node_num(self.category_tree)}->{calc_node_num(category_tree_pruned)}.")

        self.category_tree = category_tree_pruned
        self.save_tree("pruned.bin")
        return self.category_tree

    def _check_category_validity(self, id):
        if id in self.is_valid:
            return self.is_valid[id]

        if len(self.category_tree[id]) == 0:
            self.is_valid[id] = (id in self.main_topic_id)
            return self.is_valid

        for child in self.category_tree[id]:
            self._check_category_validity(child)

        valid = []
        for child in self.category_tree[id]:
            assert child in self.is_valid
            valid.append(self._check_category_validity(child))
        self.is_valid[id] = np.any(valid)
        return self.is_valid[id]

    def _generate_reverse_tree(self):
        category_tree_rev = {}
        for wikiid in self.category_tree:
            for child in self.category_tree[wikiid]:
                if child not in category_tree_rev:
                    category_tree_rev[child] = set()
                category_tree_rev[child].add(wikiid)
        self.category_tree_rev = category_tree_rev
        print(f"Reverse tree (category -> sub-category): "
              f"Tree size (|V|+|E|): {calc_tree_size(category_tree_rev)} "
              f"| # of categories: {calc_node_num(category_tree_rev)}.")
        return self.category_tree_rev

    def _reset_temp(self):
        global num_cat, num_file, wikiid_tmpid_map
        num_cat = 0
        num_file = 0
        wikiid_tmpid_map = {}

    def save_category_postings(self):
        # save the 'category postings', i.e. wikiid (category) -> docid;docid;docid;...
        self._reset_temp()
        self._generate_reverse_tree()
        for wikiid in self.main_topic_id:
            if wikiid not in self.category_tree_rev: continue
            if not self.is_valid[wikiid]: continue
            self._dfs_on_rev(wikiid)
        self.write_tree.write_cat_postings_buffer()
        self.write_tree.write_cat_postings_id_info()

    def _dfs_on_rev(self, id):
        global num_cat, wikiid_tmpid_map, MAX_LINE, cat_postings_buffer, num_file

        if id in wikiid_tmpid_map:
            if id in cat_postings_buffer:
                return cat_postings_buffer[id]

            tmpid = wikiid_tmpid_map[id]
            assert tmpid < num_cat
            file_id = wikiid_tmpid_map[id] // MAX_LINE
            line = linecache.getline(osp.join(self.output_folder, f"cat_postings_{file_id}.txt"),
                                     tmpid % MAX_LINE + 1)

            line = line.strip().split("-")[1]
            if len(line) == 0:
                postings = []
            else:
                postings = [int(item) for item in line.split(";")]

            return postings

        if id not in self.category_tree_rev:  # leaf node (wiki article)
            cat_postings_buffer[id] = []
            wikiid_tmpid_map[id] = num_cat
            num_cat += 1
            if num_cat % 10000 == 0:
                print(num_cat)

            if num_cat % MAX_LINE == 0:
                self.write_tree.write_cat_postings_buffer()
                cat_postings_buffer = {}
                num_file += 1

            return []

        # buffer category postings info into a file
        for subcat in self.category_tree_rev[id]:
            self._dfs_on_rev(subcat)

        postings = set()
        for subcat in self.category_tree_rev[id]:
            assert subcat in wikiid_tmpid_map
            if subcat not in self.category_tree_rev:  # a wiki article
                postings.add(subcat)
            postings.update(self._dfs_on_rev(subcat))

        cat_postings_buffer[id] = sorted(postings)
        wikiid_tmpid_map[id] = num_cat
        num_cat += 1
        if num_cat % 10000 == 0:
            print(num_cat)
        if num_cat % MAX_LINE == 0:
            self.write_tree.write_cat_postings_buffer()
            cat_postings_buffer = {}
            num_file += 1

    def save_page_categories(self):
        self._reset_temp()
        # cache the descendent (category) of each node
        for wikiid in self.all_wiki_id:
            if not self.is_valid[wikiid]: continue
            self._dfs(wikiid)
        self.write_tree.write_descendent_buffer()
        self.write_tree.write_descendent_id_info()

    def _dfs(self, id):
        global num_cat, wikiid_tmpid_map, MAX_LINE, descendent_buffer, num_file

        if id in wikiid_tmpid_map:
            if id in descendent_buffer:
                return descendent_buffer[id]

            tmpid = wikiid_tmpid_map[id]
            assert tmpid < num_cat
            file_id = wikiid_tmpid_map[id] // MAX_LINE
            line = linecache.getline(osp.join(self.output_folder, f"descendents_{file_id}.txt"),
                                     tmpid % MAX_LINE + 1)

            line = line.strip().split("-")[1]
            if len(line) == 0:
                des = []
            else:
                des = [int(item) for item in line.split(";")]

            return des

        if len(self.category_tree[id]) == 0:
            descendent_buffer[id] = []
            wikiid_tmpid_map[id] = num_cat
            num_cat += 1
            if num_cat % 10000 == 0:
                print(num_cat)

            if num_cat % MAX_LINE == 0:
                self.write_tree.write_descendent_buffer()
                descendent_buffer = {}
                num_file += 1

            return []

        # buffer descendent info into a file
        for child in self.category_tree[id]:
            self._dfs(child)

        des = set()
        for child in self.category_tree[id]:
            assert child in wikiid_tmpid_map
            des.add(child)
            des.update(self._dfs(child))

        descendent_buffer[id] = sorted(des)
        wikiid_tmpid_map[id] = num_cat
        num_cat += 1
        if num_cat % 10000 == 0:
            print(num_cat)
        if num_cat % MAX_LINE == 0:
            self.write_tree.write_descendent_buffer()
            descendent_buffer = {}
            num_file += 1

    def save_shortest_path(self):
        self._reset_temp()
        # docid-topic:id;id;id|topic:id;id;id ...
        for wikiid in self.all_wiki_id:
            if not self.is_valid[wikiid]: continue
            self._dfs_sp(wikiid)
        self.write_tree.write_shortest_path_buffer()
        self.write_tree.write_shortest_path_id_info()

    def _dfs_sp(self, id):
        global num_cat, wikiid_tmpid_map, MAX_LINE, shortest_paths_buffer, num_file

        if id in wikiid_tmpid_map:
            if id in shortest_paths_buffer:
                return shortest_paths_buffer[id]

            tmpid = wikiid_tmpid_map[id]
            assert tmpid < num_cat
            file_id = wikiid_tmpid_map[id] // MAX_LINE
            line = linecache.getline(osp.join(self.output_folder, f"shortest_paths_{file_id}.txt"),
                                     tmpid % MAX_LINE + 1)

            line = line.strip().split("-")[1]

            sp = {topic: None for topic in self.main_topic_id}

            if len(line) != 0:
                path_to_topics = line.split("|")
                path_to_topics = [item.split(":") for item in path_to_topics]
                for topic, path in path_to_topics:
                    topic = int(topic)
                    assert topic in sp
                    if len(path) == 0:
                        sp[topic] = []
                    else:
                        sp[topic] = [int(node) for node in path.split(";")]

            return sp

        if len(self.category_tree[id]) == 0:
            assert id in self.main_topic_id
            shortest_paths_buffer[id] = {topic: None for topic in self.main_topic_id}
            shortest_paths_buffer[id][id] = []
            wikiid_tmpid_map[id] = num_cat
            num_cat += 1
            if num_cat % 10000 == 0:
                print(num_cat)

            if num_cat % MAX_LINE == 0:
                self.write_tree.write_shortest_path_buffer()
                shortest_paths_buffer = {}
                num_file += 1

            return shortest_paths_buffer[id]

        # buffer descendent info into a file
        for child in self.category_tree[id]:
            self._dfs_sp(child)

        sp = {topic: None for topic in self.main_topic_id}
        for child in self.category_tree[id]:
            assert child in wikiid_tmpid_map
            sp_child = self._dfs_sp(child)
            for topic in self.main_topic_id:
                if sp_child[topic] is None: continue
                if sp_child[topic] is not None and sp[topic] is None:
                    sp[topic] = [child, *sp_child[topic]]
                else:
                    if len(sp_child[topic]) + 1 < len(sp[topic]):
                        sp[topic] = [child, *sp_child[topic]]

        shortest_paths_buffer[id] = sp
        wikiid_tmpid_map[id] = num_cat
        num_cat += 1
        if num_cat % 10000 == 0:
            print(num_cat)
        if num_cat % MAX_LINE == 0:
            self.write_tree.write_shortest_path_buffer()
            shortest_paths_buffer = {}
            num_file += 1


if __name__ == '__main__':
    argparser = argparse.ArgumentParser("Parse and save the tree structure")
    argparser.add_argument("--index-folder", type=str, default="../data/index",
                           help="the folder to the pre-saved index")
    argparser.add_argument("--save-folder", type=str, default="../data/tree",
                           help="the folder to save the parsed tree structure")
    args = argparser.parse_args()

    if osp.exists(args.save_folder):
        shutil.rmtree(args.save_folder)
    os.makedirs(args.save_folder)

    db = mysql_connect()
    cursor = db.cursor()

    tree_parser = TreeParser(
        input_folder=args.index_folder,
        output_folder=args.save_folder
    )

    tree_parser.get_tree(cursor)
    tree_parser.save_tree()
    # tree_parser.category_tree = load_obj(osp.join(args.save_folder, "raw.bin"))  #########
    # tree_parser.main_topic_id = mysql_fetch_main_topic_id(cursor)  #######################

    tree_parser.prune_tree()
    tree_parser.save_category_postings()
    tree_parser.save_page_categories()
    tree_parser.save_shortest_path()
    save_wikiid_title_map(cursor, tree_parser.category_tree, args.save_folder)



