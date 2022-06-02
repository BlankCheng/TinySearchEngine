import linecache
import os
import os.path as osp
import sys
sys.path.append("..")
import time
import re
from Stemmer import Stemmer
from nltk.corpus import stopwords
import numpy as np
from typing import Tuple, Union, List

from tree.utils import CategoryInfo
from search.english_search import RunQuery, FileTraverser, QueryResults
from search.english_indexer import TextPreProcessor
from utils.ranker import Ranker

from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response
from markupsafe import Markup
import json

# ====================== #
#     specify paths      #
# ====================== #
data_folder = "../data"
index_folder = osp.join(data_folder, "index")
tree_folder = osp.join(data_folder, "tree")
text_folder = osp.join(data_folder, "text")

# ====================== #
#    initialize tools    #
# ====================== #
stemmer = Stemmer('english')

with open('../data/index/num_pages.txt', 'r') as f:
    num_pages = float(f.readline().strip())

stop_words = (set(stopwords.words("english")))
html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
text_pre_processor = TextPreProcessor(html_tags, stemmer, stop_words)
file_traverser = FileTraverser()
ranker = Ranker(num_pages)
query_results = QueryResults(file_traverser)
run_query = RunQuery(text_pre_processor, file_traverser, ranker, query_results)
METHOD_MAP = {
    "TF-IDF": "weighted_field_tf_idf",
    "Field": "weighted_field_tf_idf",
    "COS": "cosine_similarity_tf_idf",
    "BM25": "bm25",
    "Cate": "category_generality"
}
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

        method_name = METHOD_MAP[method]

        page_id_list, q_correction, relevant_tokens = get_result(query, method_name)
        n_result = len(page_id_list)

        disable_previous = page == 1
        disable_next = NUM_RESULT_PER_PAGE * page >= n_result

        page_id_list = page_id_list[NUM_RESULT_PER_PAGE * (page - 1) : NUM_RESULT_PER_PAGE * page]

        results = specify_results(page_id_list, query=query, corrected_query=q_correction, relevant_tokens=relevant_tokens)

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


def get_result(query: str, method: str) -> Tuple[List, Union[None, str], List]:

    result_dict = run_query.query_api(query, method)
    ranked_results = result_dict["ranked_results"]
    print("Totally", len(ranked_results), "results.")
    corrected_query = result_dict["corrected_query"]
    relevant_tokens = result_dict["relevant_tokens"]

    ranked_docid = sorted(ranked_results.keys(), key=lambda docid: ranked_results[docid], reverse=True)
    ranked_docid = [int(docid) for docid in ranked_docid]
    if corrected_query is None:
        corrected_query = ""
    relevant_tokens = list(relevant_tokens)

    return ranked_docid, corrected_query, relevant_tokens


def specify_results(page_id_list, query, corrected_query="", relevant_tokens=None):
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
        result["page_summary"] = generate_summary(page_id, query, corrected_query, relevant_tokens)
        result["page_main_categories"] = category_info.get_page_category_hierarchy(page_id=page_id)
        result["page_main_categories"] = sorted(result["page_main_categories"], key=lambda item: len(item))
        results.append(result)
    return results


# TODO: add corrected query ...
def generate_summary(page_id, query, corrected_query="", relevant_tokens=None):
    query_words = query.split(" | ")[0].strip().split()
    if len(corrected_query) > 0:
        query_words += corrected_query.split()
    query_words = stemmer.stemWords(query_words)
    if relevant_tokens is not None:
        query_words.extend(relevant_tokens)
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
    if len(html) <= 1:
        html = raw_text[:MAX_NUM_WORD_PER_SUMMARY]

    if len(html) == 0:
        html.append("(No text)")
    else:
        if html[-1] != "...":
            html.append("...")

    html = " ".join(html)

    return Markup(html)




if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=9995)
    # app.run(debug=True)


