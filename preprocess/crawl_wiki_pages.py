import multiprocessing
import requests
import random
import os
import argparse
import json
from typing import List, Dict


def worker(pid: int, page_urls: Dict, page_dir: str):
    for page_name, page_url in page_urls.items():
        if os.path.exists(os.path.join(page_dir, f'{page_name}.html')):
            continue

        print(f'Pid#{pid}: crawling {page_name}: {page_url}')
        if random.random() < 0.01:
            print(f"Num of pages: {len(os.listdir(page_dir))}")

        try:
            page_html = requests.get(url=page_url).text
            with open(os.path.join(page_dir, f'{page_name}.html'), 'w') as f:
                f.write(page_html)
        except Exception as e:
            print(e)


def main():
    if args.category:
        categories = [args.category]
    else:
        categories = os.listdir(args.data_dir)

    for cate in categories:
        cate_dir = os.path.join(args.data_dir, cate)
        page_dir = os.path.join(args.data_dir, cate, 'pages/')
        page_url_path = os.path.join(cate_dir, 'page_url.json')
        os.makedirs(page_dir, exist_ok=True)

        with open(page_url_path, 'r') as f:
            page_urls = json.load(f)

        # split urls to processes
        page_url_splits = [dict() for _ in range(args.n_processes)]
        group = 0
        for page, url in page_urls.items():
            page_url_splits[group][page] = url
            group = (group + 1) % args.n_processes

        # multiprocess crawl
        pool = multiprocessing.Pool(processes=args.n_processes)
        for pid in range(args.n_processes):
            pool.apply_async(worker, args=(pid, page_url_splits[pid], page_dir))

        pool.close()
        pool.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # path
    parser.add_argument('--data_dir', type=str, default='../data/categories/')
    # options
    parser.add_argument('--category', type=str, default=None)
    parser.add_argument('--n_processes', type=int, default=1)

    args = parser.parse_args()

    main()

