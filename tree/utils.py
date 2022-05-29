import os
import os.path as osp
import linecache


class CategoryInfo(object):
    def __init__(self, data_folder="../data"):
        self.data_folder = data_folder

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

    def get_page_category_names(self, **kwargs):
        if "page_id" in kwargs:
            pageid = kwargs["page_id"]
            wikiid = linecache.getline(osp.join(self.data_folder, "index", "pageid_wikiid_map.txt"), pageid + 1)
            wikiid = int(wikiid.split("-")[-1])
            title = linecache.getline(osp.join(self.data_folder, "index", "pageid_title_map.txt"), pageid + 1)
            title = title.strip().split("-", 1)[-1]
            # print(pageid, wikiid, title)
            high = linecache.getline(osp.join(self.data_folder, "tree", "descendents_nline.txt"), 1)
            high = int(high)
            categories_line = self._binary_search_wikiid(str(wikiid), high,
                                                         osp.join(self.data_folder, "tree", "descendents_id_info.txt"))
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
        elif "wiki_id" in kwargs:
            wikiid = kwargs["wiki_id"]
            high = linecache.getline(osp.join(self.data_folder, "tree", "descendents_nline.txt"), 1)
            high = int(high)
            categories_line = self._binary_search_wikiid(str(wikiid), high,
                                                         osp.join(self.data_folder, "tree", "descendents_id_info.txt"))
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
        else:
            raise NotImplemented


if __name__ == '__main__':
    category_info = CategoryInfo(data_folder="../data")
    category_info.get_page_category_names(page_id=10)
    category_info.get_page_category_names(wiki_id=20460257)