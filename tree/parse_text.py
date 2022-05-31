import argparse
import os
import os.path as osp
import shutil
import xml.sax
from tqdm import tqdm
import re
import sys
import time
import json
from Stemmer import Stemmer
from nltk.corpus import stopwords
from collections import defaultdict


num_pages = 0
num_files = 0
id_info_map = {}  # docid-file-line
id_raw_map = {}
id_processed_map = {}


'''
This class takes the raw text as input and returns the preprocessed text the list of words.
Ex- raw text ----> list of words
'''


class TextProcessor():

    def __init__(self, html_tags, stemmer):
        self.html_tags = html_tags
        self.stemmer = stemmer

    def stem_text(self, text_data):
        cleaned_text = self.stemmer.stemWords(text_data)

        return cleaned_text

    def remove_html_tags(self, text_data):
        cleaned_text = re.sub(self.html_tags, ' ', text_data)

        return cleaned_text

    def process_text_deep(self, text_data: str):
        text_ori = text_data.lower().split()
        text = self.stem_text(text_ori)
        for i in range(len(text)):
            if len(text[i]) == 0:
                text[i] = text_ori[i]
        text = " ".join(text)

        return text

    def process_text_weak(self, text_data: str):
        text = text_data.strip().replace("\n", " ")
        text = self.remove_html_tags(text)
        text = re.sub('(http://[^ ]+)', ' ', text)
        text = re.sub('(https://[^ ]+)', ' ', text)
        text = re.sub('(<.*?>)', ' ', text)

        pattern = re.compile('\{{1,}.*?\}{1,}|\[{1,}.*?\]{1,}|\={2,}.*?\={2,}')
        def repl(matchobj):
            text = matchobj.group(0).strip('[]{}=')
            if re.match('^.*?:', text):
                return ' '
            else:
                return text
        text = re.sub(pattern, repl, text)

        text = text.replace(":", " ").replace("|", " ")
        text = text.replace("[[", " ").replace("]]", " ")
        text = text.replace("=", " ")
        text = text.split()
        text = " ".join(text)
        return text


class WriteData():

    def __init__(self, save_folder):

        self.save_folder = save_folder


    def write_id_raw_map(self):

        global id_raw_map, num_files
        temp_id_raw = []

        temp_id_raw_map = sorted(id_raw_map.items(), key=lambda item: int(item[0]))

        for id, raw in tqdm(temp_id_raw_map):
            t = str(id) + '-' + raw.strip()
            temp_id_raw.append(t)

        with open(osp.join(self.save_folder, f"pageid_raw_map_{num_files}.txt"), 'w') as f:
            f.write('\n'.join(temp_id_raw))
            f.write('\n')

    def write_id_processed_map(self):

        global id_processed_map, num_files
        temp_id_processed = []

        temp_id_processed_map = sorted(id_processed_map.items(), key=lambda item: int(item[0]))

        for id, processed in tqdm(temp_id_processed_map):
            t = str(id) + '-' + processed.strip()
            temp_id_processed.append(t)

        with open(osp.join(self.save_folder, f"pageid_processed_map_{num_files}.txt"), 'w') as f:
            f.write('\n'.join(temp_id_processed))
            f.write('\n')

    def write_id_info_map(self):

        global id_info_map
        temp_id_info = []

        temp_id_info_map = sorted(id_info_map.items(), key=lambda item: int(item[0]))

        for id, (file_id, line_id) in tqdm(temp_id_info_map):
            t = f"{id}-{file_id}-{line_id}"
            temp_id_info.append(t)

        with open(osp.join(self.save_folder, f"pageid_info_map.txt"), 'a') as f:
            f.write('\n'.join(temp_id_info))
            f.write('\n')


class WikiTextParser(xml.sax.ContentHandler):

    def __init__(self, text_processor: TextProcessor, write_data: WriteData):

        self.tag = ''
        self.title = ''
        self.text = ''
        self.write_data = write_data
        self.text_processor = text_processor

    def startElement(self, name, attrs):

        self.tag = name

    def endElement(self, name):
        global num_pages, num_files, id_info_map, id_raw_map, id_processed_map

        max_page_per_file = 10000

        if name == 'page':

            id_raw_map[num_pages] = self.text_processor.process_text_weak(self.text)
            id_processed_map[num_pages] = self.text_processor.process_text_deep(id_raw_map[num_pages])
            id_info_map[num_pages] = (num_files, num_pages % max_page_per_file)

            assert len(id_raw_map[num_pages].split()) == len(id_processed_map[num_pages].split())

            print(num_pages, self.title.strip())
            num_pages += 1

            self.tag = ""
            self.title = ""
            self.text = ""

            if num_pages % max_page_per_file == 0:
                # write to file
                self.write_data.write_id_info_map()
                self.write_data.write_id_raw_map()
                self.write_data.write_id_processed_map()
                id_info_map = {}
                id_raw_map = {}
                id_processed_map = {}
                num_files += 1

    def characters(self, content):

        if self.tag == 'text':
            self.text += content

        if self.tag == "title":
            self.title += content



if __name__ == '__main__':
    # default_xml = osp.expanduser("~/data/wiki-dumps/enwiki-latest-pages-articles16.xml-p20460153p20570392")
    default_xml = osp.expanduser("~/data/wiki-dumps/enwiki-latest-pages-articles10.xml-p4045403p5399366")
    # default_xml = osp.expanduser("~/lmj/Wiki-Search-Engine/dumps/test.xml")

    argparser = argparse.ArgumentParser("Parse wikipedia page id")
    argparser.add_argument("--xml-file", type=str, default=default_xml,
                        help="path to the xml file to parse")
    argparser.add_argument("--save-folder", type=str, default="../data/text",
                        help="root to saved files")
    args = argparser.parse_args()

    os.makedirs(args.save_folder, exist_ok=True)

    # clear the following files
    with open(osp.join(args.save_folder, "pageid_info_map.txt"), "w") as f:
        pass

    html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
    stemmer = Stemmer('english')

    text_processor = TextProcessor(html_tags=html_tags, stemmer=stemmer)
    write_data = WriteData(args.save_folder)

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)
    xml_parser = WikiTextParser(text_processor, write_data)
    parser.setContentHandler(xml_parser)
    output = parser.parse(args.xml_file)

    write_data.write_id_info_map()
    write_data.write_id_raw_map()
    write_data.write_id_processed_map()


    # check
    for file_id in range(num_files + 1):
        nlines = 0
        with open(osp.join(args.save_folder, f"pageid_raw_map_{file_id}.txt"), "r") as f:
            for line in f:
                nlines += 1

        print(f"file: {file_id}, nlines: {nlines}")

        nlines = 0
        with open(osp.join(args.save_folder, f"pageid_processed_map_{file_id}.txt"), "r") as f:
            for line in f:
                nlines += 1

        print(f"file: {file_id}, nlines: {nlines}")
