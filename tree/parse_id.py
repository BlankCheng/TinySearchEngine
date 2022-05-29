import argparse
import os
import os.path as osp
import xml.sax
from tqdm import tqdm


num_pages = 0
pageid_wikiid_map = {}
pageid_title_map = {}


class WriteData():

    def __init__(self, save_folder):

        self.save_folder = save_folder

    def write_id_title_map(self):

        global pageid_title_map
        temp_id_title = []

        temp_id_title_map = sorted(pageid_title_map.items(), key=lambda item: int(item[0]))

        for id, title in tqdm(temp_id_title_map):
            t = str(id) + '-' + title.strip()
            temp_id_title.append(t)

        with open(osp.join(self.save_folder, "pageid_title_map.txt"), 'a') as f:  # append mode
            f.write('\n'.join(temp_id_title))
            f.write('\n')

    def write_id_wikiid_map(self):

        global pageid_wikiid_map
        temp_id_wikiid = []

        temp_id_wikiid_map = sorted(pageid_wikiid_map.items(), key=lambda item: int(item[0]))

        for id, title in tqdm(temp_id_wikiid_map):
            t = str(id) + '-' + title.strip()
            temp_id_wikiid.append(t)

        with open(osp.join(self.save_folder, "pageid_wikiid_map.txt"), 'a') as f:  # append mode
            f.write('\n'.join(temp_id_wikiid))
            f.write('\n')

    def write_wikiid_title_map(self):

        global pageid_title_map, pageid_wikiid_map
        temp_wikiid_title = []

        temp_wikiid_title_map = sorted([(pageid_wikiid_map[id], pageid_title_map[id])
                                    for id in pageid_wikiid_map.keys()],
                                   key=lambda item: str(item[0]))

        for id, title in tqdm(temp_wikiid_title_map):
            t = str(id) + '-' + title.strip()
            temp_wikiid_title.append(t)

        with open(osp.join(self.save_folder, "wikiid_title_map.txt"), 'a') as f:  # append mode
            f.write('\n'.join(temp_wikiid_title))
            f.write('\n')


class WikiIdParser(xml.sax.ContentHandler):

    def __init__(self, write_data: WriteData):

        self.tag = ''
        self.title = ''
        self.wikiid = ''
        self.block_content = False  # block the content in <revision>...</revision>
        self.write_data = write_data

    def startElement(self, name, attrs):

        self.tag = name

        if self.tag == "revision":
            self.block_content = True

    def endElement(self, name):
        global num_pages, pageid_title_map, pageid_wikiid_map

        if name == 'page':

            pageid_title_map[num_pages] = self.title.strip()  # doc_id: title string
            pageid_wikiid_map[num_pages] = self.wikiid.strip()  # doc_id: wiki_id string

            print(num_pages, self.title.strip(), self.wikiid.strip())
            num_pages += 1

            self.tag = ""
            self.title = ""
            self.wikiid = ""

            if num_pages % 40000 == 0:
                # write to file
                self.write_data.write_id_title_map()
                self.write_data.write_id_wikiid_map()
                self.write_data.write_wikiid_title_map()
                pageid_title_map = {}
                pageid_wikiid_map = {}

        if name == "revision":
            self.block_content = False

    def characters(self, content):

        if not self.block_content:

            if self.tag == 'title':
                self.title += content

            if self.tag == "id":
                self.wikiid += content


if __name__ == '__main__':
    default_xml = osp.expanduser("~/data/wiki-dumps/enwiki-latest-pages-articles16.xml-p20460153p20570392")
    # default_xml = osp.expanduser("~/data/wiki-dumps/enwiki-latest-pages-articles10.xml-p4045403p5399366")
    # default_xml = osp.expanduser("~/lmj/Wiki-Search-Engine/dumps/test.xml")

    argparser = argparse.ArgumentParser("Parse wikipedia page id")
    argparser.add_argument("--xml-file", type=str, default=default_xml,
                        help="path to the xml file to parse")
    argparser.add_argument("--save-folder", type=str, default="../data/index",
                        help="root to saved files")
    args = argparser.parse_args()
    os.makedirs(args.save_folder, exist_ok=True)

    # clear the following files
    with open(osp.join(args.save_folder, "pageid_wikiid_map.txt"), "w") as f:
        pass
    with open(osp.join(args.save_folder, "pageid_title_map.txt"), "w") as f:
        pass

    write_data = WriteData(args.save_folder)

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)
    xml_parser = WikiIdParser(write_data)
    parser.setContentHandler(xml_parser)
    output = parser.parse(args.xml_file)

    write_data.write_id_title_map()
    write_data.write_id_wikiid_map()
    write_data.write_wikiid_title_map()

    print("num pages:", num_pages)




