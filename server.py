import linecache
import os
import os.path as osp
import time
from Stemmer import Stemmer
import numpy as np
from typing import Tuple, Union
from tree.utils import CategoryInfo

from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response
from markupsafe import Markup
import json


data_folder = "./data"
index_folder = osp.join(data_folder, "index")
tree_folder = osp.join(data_folder, "tree")
text_folder = osp.join(data_folder, "text")
stemmer = Stemmer('english')
NUM_RESULT_PER_PAGE = 20
MAX_NUM_WORD_PER_SUMMARY = 100


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
        page = int(page)
        if page <= 0:
            page = 1

        t0 = time.time()

        q_correction, page_id_list = get_result(query, method)
        n_result = len(page_id_list)

        disable_previous = page == 1
        disable_next = NUM_RESULT_PER_PAGE * page >= n_result

        page_id_list = page_id_list[NUM_RESULT_PER_PAGE * (page - 1) : NUM_RESULT_PER_PAGE * page]

        results = specify_results(page_id_list, query=query)

        t_search = f"{time.time() - t0:.6}"

        return render_template("search.html",
                               query=query, method=method,
                               results=results, n_result=n_result,
                               t_search=t_search,
                               q_correction=q_correction,
                               disable_previous=disable_previous,
                               disable_next=disable_next)
    else:
        return redirect(url_for("render_index"))


def get_result(query: str, method: str) -> Tuple[Union[None, str], Tuple]:
    time.sleep(0.5)
    return "shit", (5, 8, 9, 10, 11, 12, 13) * 5


def specify_results(page_id_list, query):
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
        result["page_summary"] = generate_summary(page_id, query)
        result["page_main_categories"] = category_info.get_page_category_hierarchy(page_id=page_id)  # TODO
        results.append(result)
    return results


def generate_summary(page_id, query):
    query_words = query.split(" | ")[0].strip().split()
    query_words = stemmer.stemWords(query_words)
    line = linecache.getline(osp.join(text_folder, "pageid_info_map.txt"), page_id + 1)
    _, file_id, line_id = line.split("-")
    file_id = int(file_id)
    line_id = int(line_id)

    raw_text = linecache.getline(osp.join(text_folder, f"pageid_raw_map_{file_id}.txt"), line_id + 1)
    raw_text = raw_text.split("-", 1)[1]
    raw_text = raw_text.split()

    text = linecache.getline(osp.join(text_folder, f"pageid_processed_map_{file_id}.txt"), line_id + 1)
    text = text.split("-", 1)[1]
    text = text.split()

    wrap = lambda t: '<text style="color: red;">' + t + '</text>'

    flag_id = []
    for i in range(len(text)):
        for q in query_words:
            if q == text[i]:
                flag_id.append(i)
                break

    for i in flag_id:
        raw_text[i] = wrap(raw_text[i])

    selected = np.array([False for _ in range(len(raw_text))], dtype=bool)
    for i in flag_id:
        selected[max(0, i-4):i+10] = True

    html = []
    for i in range(len(raw_text)):
        if not selected[i]:
            if len(html) == 0 or html[-1] != "...":
                html.append("...")
        else:
            html.append(raw_text[i])
        if len(html) > MAX_NUM_WORD_PER_SUMMARY:
            break
    if len(html) == 1:
        html = raw_text[:MAX_NUM_WORD_PER_SUMMARY]

    if html[-1] != "...":
        html.append("...")

    html = " ".join(html)

    return Markup(html)




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=9995)
    # app.run(debug=True)


