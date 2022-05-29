from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import os
import json
import argparse
import random

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}

def crawl_single_page(root_url, r_drop=5.0, max_pages=None):
    """
    To crawl the sub-categories and linked pages in a given url
    :param root_url: str, a given url
    :return: Dict, sub-category -> url; Dict, linked-page -> url
    """

    while True:
        try:
            print(f"\tCrawling {root_url} ...")
            html = urlopen(Request(root_url, headers=HEADERS), timeout=2.0)
            soup = BeautifulSoup(html, 'html.parser')
            print(f"\tSuccess!")
            break
        except BaseException:
            pass

    subcats = {}
    pages = {}

    # 1. crawl sub-categories of the current category
    mw_subcategories = soup.find_all("div", {"id": "mw-subcategories"})
    if len(mw_subcategories) != 0:
        mw_subcategories = mw_subcategories[0]

        mw_category_groups = mw_subcategories.find_all("div", {"class": "mw-category-group"})
        num_subcat = 0
        for group in mw_category_groups:
            if not str(group.h3.text).isalpha(): continue
            bodys = group.find_all("div", {"class": "CategoryTreeItem"})
            num_subcat += len(bodys)
            for body in bodys:
                kw = body.find("a")
                href = kw["href"]
                contents = kw.text
                kw = str(contents)
                if kw not in subcats:
                    subcats[kw] = "https://en.wikipedia.org" + href
        print(f"\t{num_subcat} sub-categories in total.")

    # 2. crawl pages linked to the current category
    mw_pages = soup.findAll("div", {"id": "mw-pages"})
    if len(mw_pages) != 0:
        mw_pages = mw_pages[0]
        bodys = mw_pages.findAll("li")
        print(f"\t{len(bodys)} linked pages in total.")
        for body in bodys:
            kw = body.find("a")
            href = kw["href"]
            contents = kw.text
            kw = str(contents)
            if kw not in pages:
                pages[kw] = "https://en.wikipedia.org" + href

    # drop sub-categories
    if len(subcats) == 0 or len(pages) / len(subcats) > r_drop:
        print("\tDrop sub-categories.")
        subcats = {}

    # drop linked pages
    if max_pages is not None and len(pages) > max_pages:
        print(f"\tRandomly select {max_pages} pages.")
        pages = {k: pages[k] for k in sorted(random.sample(list(pages.keys()), max_pages))}

    return subcats, pages


def save_json(obj, save_path):
    with open(save_path, "w") as f:
        json.dump(obj, f, indent=4)


if __name__ == '__main__':
    # main_categories = ["Food and drink", "Business", "Culture", "Economy", "Engineering",
    #                    "Health", "Internet", "People", "Music", "Technology"]

    parser = argparse.ArgumentParser("wikipedia basic info crawler")
    parser.add_argument("--root", default="Food and drink")
    parser.add_argument("--r-drop", type=float, default=5.0)
    parser.add_argument("--early-stop", action="store_true")
    parser.add_argument("--stop-criterion", type=int, default=None)
    parser.add_argument("--max-pages-each-cat", type=int, default=50)
    args = parser.parse_args()

    main_categories = [args.root]

    if args.early_stop:
        save_folder = f"./saved-raw_r={args.r_drop}" \
                      f"_early-stop={args.early_stop}_{args.stop_criterion}" \
                      f"_max-pages={args.max_pages_each_cat}" \
                      f"/{args.root}"
    else:
        save_folder = f"./saved-raw_r={args.r_drop}_early-stop={args.early_stop}/{args.root}"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    explored_cat_url = {}
    cat_url = {}
    page_url = {}
    cat_to_subcats = {}
    cat_to_pages = {}

    frontier = [category for category in main_categories]
    explored = []
    enough = False

    for category in main_categories:
        cat_url[category] = f"https://en.wikipedia.org/wiki/Category:{category.replace(' ', '_')}"

    while len(frontier) > 0:
        category = frontier.pop(0)
        if category in explored:
            continue
        explored.append(category)
        if args.early_stop and len(explored) + len(frontier) > args.stop_criterion:
            enough = True
        print(f"Crawling {category} ...")

        subcats, pages = crawl_single_page(root_url=cat_url[category], r_drop=args.r_drop,
                                           max_pages=args.max_pages_each_cat)
        explored_cat_url[category] = cat_url[category]
        cat_url.update(subcats)
        page_url.update(pages)
        cat_to_subcats[category] = list(subcats.keys())
        cat_to_pages[category] = list(pages.keys())

        if args.early_stop and enough:
            print(f"\nProgress: {len(explored)} / {len(frontier) + len(explored)}\n")
        else:
            for subcat in list(subcats.keys()):
                if subcat not in frontier and subcat not in explored:
                    frontier.append(subcat)

        if len(explored) % 50 == 1:
            print(f"{len(frontier)} pages to be crawled")
            save_json(main_categories, os.path.join(save_folder, "main_categories.json"))
            save_json(cat_url, os.path.join(save_folder, "cat_url.json"))
            save_json(explored_cat_url, os.path.join(save_folder, "explored_cat_url.json"))
            save_json(page_url, os.path.join(save_folder, "page_url.json"))
            save_json(cat_to_subcats, os.path.join(save_folder, "cat_to_subcats.json"))
            save_json(cat_to_pages, os.path.join(save_folder, "cat_to_pages.json"))

    save_json(main_categories, os.path.join(save_folder, "main_categories.json"))
    save_json(cat_url, os.path.join(save_folder, "cat_url.json"))
    save_json(explored_cat_url, os.path.join(save_folder, "explored_cat_url.json"))
    save_json(page_url, os.path.join(save_folder, "page_url.json"))
    save_json(cat_to_subcats, os.path.join(save_folder, "cat_to_subcats.json"))
    save_json(cat_to_pages, os.path.join(save_folder, "cat_to_pages.json"))


