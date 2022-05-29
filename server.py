import linecache
import os
import os.path as osp
import time

import numpy as np
from typing import Tuple, Union
from tree.utils import CategoryInfo

from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response
import json


data_folder = "./data"
index_folder = osp.join(data_folder, "index")
tree_folder = osp.join(data_folder, "tree")
NUM_RESULT_PER_PAGE = 20

app = Flask(__name__, static_folder="./demo/static", template_folder="./demo/template")


@app.route("/")
def render_index():
    return render_template("index.html")


@app.route("/search")
def search():
    if request.args:
        query = str(request.args.get("q"))
        method = str(request.args.get("m"))
        page = str(request.args.get("p"))
        if page == "None":
            page = 1
        if page <= 0:
            page = 1
        t0 = time.time()

        q_correction, page_id_list = get_result(query, method)
        n_result = len(page_id_list)

        page_id_list = page_id_list[NUM_RESULT_PER_PAGE * (page - 1) : NUM_RESULT_PER_PAGE * page]

        results = specify_results(page_id_list)

        t_search = f"{time.time() - t0:.6}"

        return render_template("search.html",
                               query=query, method=method,
                               results=results, n_result=n_result,
                               t_search=t_search,
                               q_correction=q_correction)
    else:
        return redirect(url_for("render_index"))


def get_result(query: str, method: str) -> Tuple[Union[None, str], Tuple]:
    time.sleep(0.5)
    return "shit", (5, 8, 9, 10, 11, 12, 13)


def specify_results(page_id_list):
    category_info = CategoryInfo(data_folder)
    results = []
    for page_id in page_id_list:
        result = {}
        result["page_id"] = page_id
        result["page_title"] = linecache.getline(osp.join(index_folder, "pageid_title_map.txt"), page_id + 1)
        if result["page_title"] is None:
            continue
        else:
            result["page_title"] = result["page_title"].strip().split("-", 1)[1]
        result["page_url"] = "https://en.wikipedia.org/wiki/" + result["page_title"].replace(" ", "_")
        result["page_summary"] = f"Fuck you! " * 50   # TODO
        result["page_main_categories"] = category_info.get_page_category_hierarchy(page_id=page_id)  # TODO
        if len(result["page_main_categories"]) > 0:
            result["page_main_categories"] = result["page_main_categories"][0]
        results.append(result)
    return results





if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=9995)
    # app.run(debug=True)


