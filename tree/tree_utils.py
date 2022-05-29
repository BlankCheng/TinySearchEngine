import time
from typing import List, Dict
from mysql_utils import *


def backtrack(cursor, page_id: int, root_ids: List, category_tree: Dict = None):

    lower_layer = {page_id}
    links = {}
    lower_all = {}  # lower layers, use dict to speed up

    while len(lower_layer) > 0:

        for child in lower_layer:
            lower_all[child] = None  # placeholder

        upper_layer = set()
        for child in lower_layer:
            if child not in links:  # update the BFS graph
                links[child] = set()
            if child in category_tree or child in root_ids:  # reach leaf OR already explored in the tree
                continue

            parents = mysql_fetch_parent_page_id(cursor, child)
            for parent in parents:
                if parent in lower_all:  # cause loop
                    continue
                links[child].add(parent)
                upper_layer.add(parent)

        lower_layer = upper_layer

    # update category tree
    for child, parents in links.items():
        if child not in category_tree:
            category_tree[child] = set()
        category_tree[child].update(parents)

    return category_tree


def bfs(tree, source):
    to_explore = [source]
    while len(to_explore) > 0:
        print(len(to_explore))
        current = to_explore[0]
        to_explore = to_explore[1:]
        if current in tree.keys():
            to_explore.extend(tree[current])
    return


def calc_tree_size(tree):
    return sum(len(v) + 1 for v in tree.values())


def calc_node_num(tree):
    return len(tree)


def _test_time(cursor, root_ids, max_id=10**7, print_freq=1000):
    valid_cnt = 0
    i = 0
    category_tree = {}
    t0 = time.time()
    while valid_cnt < max_id:
        title = mysql_fetch_page_title(cursor=cursor, page_id=i, verbose=0)
        i += 1
        if len(title) > 0:
            continue
        valid_cnt += 1
        backtrack(cursor, page_id=i, root_ids=root_ids, category_tree=category_tree)
        if valid_cnt % print_freq == 0:
            print(f"Processed {valid_cnt} pages, time elapsed: {time.time() - t0:.2f} seconds. "
                  f"| Tree size (|V|+|E|): {calc_tree_size(category_tree)}.")
    print(f"Processed {valid_cnt} pages, time elapsed: {time.time() - t0:.2f} seconds. "
          f"| Tree size (|V|+|E|): {calc_tree_size(category_tree)}.")


if __name__ == '__main__':
    from pprint import pprint

    db = mysql_connect()

    cursor = db.cursor()

    root_ids = mysql_fetch_main_topic_id(cursor)


    # _test_time(cursor, root_ids, max_id=10**6, print_freq=1000)
    # exit()


    category_tree = {}

    t0 = time.time()

    backtrack(cursor, page_id=10, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=25520560, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=34049574, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=12, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=14, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=15, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=18, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=694860, root_ids=root_ids, category_tree=category_tree)
    backtrack(cursor, page_id=13348208, root_ids=root_ids, category_tree=category_tree)

    t1 = time.time()

    print("tree size:", calc_tree_size(category_tree), "| # nodes:", calc_node_num(category_tree))
    print(f"finished in {t1 - t0:.2f} seconds.")
    # bfs(category_tree, source=14)
    # print(mysql_fetch_page_title(cursor, 63587970))



