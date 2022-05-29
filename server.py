import os
import os.path as osp
import numpy as np

from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response
import json


app = Flask(__name__, static_folder="./demo/static", template_folder="./demo/template")


@app.route("/")
def render_index():
    return render_template("index.html")


@app.route("/search")
def search():
    if request.args:
        query = str(request.args.get("q"))
        method = str(request.args.get("m"))
        return render_template("search.html",
                               query=query, method=method,
                               results=get_dummy_results(query),
                               n_result=100, t_search=0.01,
                               q_correction="shit")
    else:
        return redirect(url_for("render_index"))


def get_dummy_results(query):
    return [{
        "page_id": 123456,
        "page_url": "https://xxx.xxx.xxx/yy/zz",
        "page_title": "This is a title",
        "page_summary": f"This is {' and '.join(query.split())}. " * 50,
        "page_main_categories": ["Economics", "Food"]
    }] * 10


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=9995)
    # app.run(debug=True)


