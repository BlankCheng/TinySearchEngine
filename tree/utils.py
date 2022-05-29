import os
import os.path as osp
import linecache
from tqdm import tqdm


class CategoryInfo(object):
    def __init__(self, data_folder="../data"):
        self.data_folder = data_folder
        if not osp.exists(osp.join(data_folder, "tree", "title_wikiid_map")):
            os.makedirs(osp.join(data_folder, "tree", "title_wikiid_map"))
            self._process_category_name_id_map()
        if not osp.exists(osp.join(self.data_folder, "tree", "processed_cat_postings")):
            os.makedirs(osp.join(self.data_folder, "tree", "processed_cat_postings"))
            self._process_category_postings()

    def _binary_search_wikiid(self, inp_wikiid, high, filename):

        low = 0
        while low < high:
            mid = (low + high) // 2
            line = linecache.getline(filename, mid)
            wikiid = line.split('-', 1)[0]

            if inp_wikiid == wikiid:
                return line

            elif inp_wikiid > wikiid:
                low = mid + 1

            else:
                high = mid

        return None

    def _binary_search_title(self, inp_title, high, filename):

        low = 0
        while low < high:
            mid = (low + high) // 2
            line = linecache.getline(filename, mid)
            title = line.split('-', 1)[0]

            if inp_title == title:
                return line

            elif inp_title > title:
                low = mid + 1

            else:
                high = mid

        return None

    def _get_wikiid_by_pageid(self, pageid):
        wikiid = linecache.getline(osp.join(self.data_folder, "index", "pageid_wikiid_map.txt"), pageid + 1)
        wikiid = int(wikiid.split("-")[-1])
        return wikiid

    def get_page_category_names(self, **kwargs):
        if "page_id" in kwargs:
            pageid = kwargs["page_id"]
            wikiid = self._get_wikiid_by_pageid(pageid)
            title = linecache.getline(osp.join(self.data_folder, "index", "pageid_title_map.txt"), pageid + 1)
            title = title.strip().split("-", 1)[-1]
        elif "wiki_id" in kwargs:
            wikiid = kwargs["wiki_id"]
        else:
            raise NotImplementedError

        high = linecache.getline(osp.join(self.data_folder, "tree", "descendents_nline.txt"), 1)
        high = int(high)
        categories_line = self._binary_search_wikiid(str(wikiid), high,
                                                     osp.join(self.data_folder, "tree", "descendents_id_info.txt"))
        if categories_line is None:
            return []
        # print(categories_line)
        _, file_num, line_num = categories_line.split("-")
        file_num = int(file_num)
        line_num = int(line_num)
        category_wikiid_list = linecache.getline(osp.join(self.data_folder, "tree", f"descendents_{file_num}.txt"),
                                                 line_num + 1)
        category_wikiid_list = category_wikiid_list.strip().split("-")[-1].split(";")

        category_name_list = [self._binary_search_wikiid(category_wikiid, high,
                                                         osp.join(self.data_folder, "tree", "wikiid_title_map.txt"))
                              for category_wikiid in category_wikiid_list]
        category_name_list = [category_name.strip().split("-")[-1] for category_name in category_name_list]
        return category_name_list

    # optimized
    def get_category_pageid(self, category_name):
        category_name = category_name.lower().replace("-", " ").replace("_", " ")
        char_list = [chr(i) for i in range(97, 123)]
        num_list = [str(i) for i in range(0, 10)]
        ch = category_name[0]
        if ch not in num_list and ch not in char_list:
            ch = "other"
        high = linecache.getline(osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}_nline.txt"), 1)
        high = int(high)
        wikiid = self._binary_search_wikiid(category_name, high,
                                            osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}.txt"))
        if wikiid is None:
            return []
        wikiid = wikiid.strip().split("-")[-1]
        # print(wikiid)

        high = linecache.getline(osp.join(self.data_folder, "tree", "cat_postings_nline.txt"), 1)
        high = int(high)
        postings_line = self._binary_search_wikiid(str(wikiid), high,
                        osp.join(self.data_folder, "tree", "cat_postings_id_info.txt"))
        if postings_line is None:
            return []
        _, file_num, line_num = postings_line.split("-")
        file_num = int(file_num)
        line_num = int(line_num)
        # print(file_num, line_num)
        pageids = linecache.getline(osp.join(self.data_folder, "tree", "processed_cat_postings", f"{file_num}.txt"),
                                     line_num + 1)
        pageids = pageids.split("-", 1)[1].split(";")
        pageids = [int(item) for item in pageids]
        # print(len(pageids))
        return pageids

    def get_page_category_hierarchy(self, **kwargs):
        if "page_id" in kwargs:
            pageid = kwargs["page_id"]
            wikiid = self._get_wikiid_by_pageid(pageid)
            title = linecache.getline(osp.join(self.data_folder, "index", "pageid_title_map.txt"), pageid + 1)
            title = title.strip().split("-", 1)[-1]
        elif "wiki_id" in kwargs:
            wikiid = kwargs["wiki_id"]
        else:
            raise NotImplementedError

        high = linecache.getline(osp.join(self.data_folder, "tree", "shortest_paths_nline.txt"), 1)
        high = int(high)
        paths_line = self._binary_search_wikiid(str(wikiid), high,
                     osp.join(self.data_folder, "tree", "shortest_paths_id_info.txt"))
        if paths_line is None:
            return []
        # print(paths_line)
        _, file_num, line_num = paths_line.split("-")
        file_num = int(file_num)
        line_num = int(line_num)
        print(file_num, line_num)

        paths = linecache.getline(osp.join(self.data_folder, "tree", f"shortest_paths_{file_num}.txt"),
                                           line_num + 1).strip()
        paths = paths.split("-")[1].split("|")
        for i in range(len(paths)):
            path = paths[i]
            topic, path = path.split(":")
            path = [int(node) for node in path.split(";")]
            path_ = []
            for node in path:
                category_name = self._binary_search_wikiid(str(node), high,
                                osp.join(self.data_folder, "tree", "wikiid_title_map.txt")).strip()
                if category_name is None:
                    continue
                else:
                    path_.append(category_name.split("-", 1)[1])
            paths[i] = path_[::-1]
        return paths

    def _process_category_name_id_map(self):
        print("Processing category name -> wiki id mapping ...")
        char_list = [chr(i) for i in range(97, 123)]
        num_list = [str(i) for i in range(0, 10)]
        wikiid_name_map_f = open(osp.join(self.data_folder, "tree", "wikiid_title_map.txt"), "r")
        for ch in char_list + num_list + ["other"]:
            with open(osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}.txt"), "w") as f: pass
        while True:
            line = wikiid_name_map_f.readline().strip()
            if len(line) == 0:
                break
            wikiid, title = line.strip().split("-", 1)
            title = title.lower().replace("_", " ").replace("-", " ")
            ch = title[0]
            if ch not in num_list and ch not in char_list:
                ch = "other"
            with open(osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}.txt"), "a") as f:
                f.write(title + f"-{wikiid}\n")
        wikiid_name_map_f.close()

        for ch in tqdm(char_list + num_list + ["other"]):
            with open(osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}.txt"), "r") as f:
                lines = f.readlines()
                lines = [line.strip().split("-") for line in lines]
                lines = sorted(lines, key=lambda item: item[0])
            with open(osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}.txt"), "w") as f:
                for line in lines:
                    f.write("-".join(line) + "\n")
            with open(osp.join(self.data_folder, "tree", "title_wikiid_map", f"{ch}_nline.txt"), "w") as f:
                f.write(f"{len(lines)}" + "\n")

    def _process_category_postings(self):
        cat_postings_files = filter(lambda fn: fn.startswith("cat_postings")
                                               and "nline" not in fn
                                               and "info" not in fn,
                                    os.listdir(osp.join(self.data_folder, "tree")))
        for cat_postings_file in cat_postings_files:
            print("Processing", cat_postings_file)
            filename = cat_postings_file.split("_")[-1]
            cat_postings_file = osp.join(self.data_folder, "tree", cat_postings_file)
            original = open(cat_postings_file, "r")
            processed = open(osp.join(self.data_folder, "tree", "processed_cat_postings", filename), "w")

            while True:

                postings = original.readline().strip()
                if len(postings) == 0:
                    break

                wikiid = postings.split("-", 1)[0]
                postings = postings.split("-", 1)[1]
                if len(postings) == 0:
                    postings = []
                else:
                    postings = postings.split(";")
                    postings = [int(item) for item in postings]

                high = linecache.getline(osp.join(self.data_folder, "index", "num_pages.txt"), 1)
                high = int(high.strip())
                pageids = [self._binary_search_wikiid(str(posting_item), high,
                                                      osp.join(self.data_folder, "index", "wikiid_pageid_map.txt"))
                           for posting_item in postings]
                pageids = filter(lambda pageid: pageid is not None, pageids)
                pageids = [int(pageid.strip().split("-")[1]) for pageid in pageids]

                processed.write(str(wikiid) + "-" + ";".join([str(pageid) for pageid in pageids]) + "\n")

            original.close()


if __name__ == '__main__':
    import time
    category_info = CategoryInfo(data_folder="../data")
    t0 = time.time()
    # for i in range(0, 100):
    #     print(category_info.get_page_category_names(page_id=i))
    print(len(category_info.get_category_pageid(category_name="Economy")))
    print(len(category_info.get_category_pageid(category_name="drinks")))
    print(len(category_info.get_category_pageid(category_name="economic sectors")))
    print(len(category_info.get_category_pageid(category_name="Economic sectors")))
    print(len(category_info.get_category_pageid(category_name="Economic_sectors")))
    print(len(category_info.get_category_pageid(category_name="LGBT and the economy")))
    # for pageid in category_info.get_category_pageid(category_name="LGBT and the economy"):
    #     print(linecache.getline(osp.join("../data/index/pageid_title_map.txt"), pageid + 1).strip())

    print(category_info.get_page_category_hierarchy(wiki_id=15002023))

    print(f"Finished in {time.time() - t0} seconds.")