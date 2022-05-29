import json
from crawl_raw_info import crawl_single_page

subcats, _ = crawl_single_page("https://en.wikipedia.org/wiki/Category:Main_topic_classifications", r_drop=99999)

subcat_names = [k.replace(" ", "_") for k in subcats.keys()]

with open("./main_topics.json", "w") as f:
    json.dump(subcat_names, f, indent=4)
