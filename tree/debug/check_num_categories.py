import os
import os.path as osp
import sys
sys.path.append("..")
import pickle
from tqdm import tqdm

from mysql_utils import mysql_connect, mysql_fetch_page_type, mysql_fetch_main_topic_id


def save_obj(obj, path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':
    raw_tree = load_obj(osp.expanduser("~/lmj/TinySearchEngine/data/tree/raw.bin"))
    pruned_tree = load_obj(osp.expanduser("~/lmj/TinySearchEngine/data/tree/pruned.bin"))

    print(len(raw_tree), len(pruned_tree))  # 1152357 568449

    db = mysql_connect(config_path="../mysql_config.json")
    cursor = db.cursor()

    main_topic_id = mysql_fetch_main_topic_id(cursor)

    num_categories = 0
    num_main_categories = 0
    for page_id in tqdm(pruned_tree):
        ns = mysql_fetch_page_type(cursor, page_id=page_id)
        if ns == 14:
            num_categories += 1
        if page_id in main_topic_id:
            num_main_categories += 1
    print("num categories:", num_categories)
    print("num main topics:", num_main_categories)

    # num categories: 409006
    # num main topics: 41


    print(len(pruned_tree))