import math
import argparse
import linecache
import time
from collections import Counter
import sys

from search.english_indexer import *
from utils.checker import Checker
from utils.ranker import Ranker
from tree.utils import CategoryFilter

print(sys.path)

'''
This class traverses various index files and return the required data
'''
class FileTraverser():

    def __init__(self):

        pass

    def binary_search_token_info(self, high, filename, inp_token):

        low = 0
        while low < high:
            mid = (low + high) // 2
            line = linecache.getline(filename, mid)
            token = line.split('-')[0]

            if inp_token == token:
                token_info = line.split('-')[1:-1]
                return token_info

            elif inp_token > token:
                low = mid + 1

            else:
                high = mid

        return None

    def binary_search_wild_card_info(self, high, filename, perm_token, num_results=5):

        low = 0
        len_prefix = len(perm_token)
        result_row = -1
        while low <= high:

            mid = (low + high) // 2
            line = linecache.getline(filename, mid)
            token = line.split('-')[0]
            if perm_token == token:
                result_row = mid
                break
            elif token > perm_token:
                if token[:len_prefix] == perm_token:
                    result_row = mid
                high = mid - 1

            else:
                low = mid + 1
        if result_row == -1:
            return None
        lines = []
        line = linecache.getline(filename, result_row)
        tokens = line.split('-')[:-1]
        while tokens[0][:len(perm_token)] == perm_token:
            lines.append(tokens[1:])
            result_row += 1
            line = linecache.getline(filename, result_row)
            tokens = line.split('-')[:-1]
        lines.sort(key=lambda x: int(x[2]), reverse=True)
        if not num_results:
            return lines
        return lines[:num_results]

    def title_search(self, page_id):

        title = linecache.getline('../data/index/id_title_map.txt', int(page_id)+1).strip()
        title = title.split('-', 1)[1]

        return title


    def search_field_file(self, field, file_num, line_num):

        if line_num != '':
            line = linecache.getline(f'../data/index/{field}_data_{str(file_num)}.txt', int(line_num)).strip()
            postings = line.split('-')[1]

            return postings

        return ''

    def get_token_info(self, token):

        char_list = [chr(i) for i in range(97,123)]
        num_list = [str(i) for i in range(0,10)]

        if token[0] in char_list:
            with open(f'../data/index/tokens_info_{token[0]}_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())

            tokens_info_pointer = f'../data/index/tokens_info_{token[0]}.txt'
            token_info = self.binary_search_token_info(num_tokens, tokens_info_pointer, token)

        elif token[0] in num_list:
            with open(f'../data/index/tokens_info_{token[0]}_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())

            tokens_info_pointer = f'../data/index/tokens_info_{token[0]}.txt'
            token_info = self.binary_search_token_info(num_tokens, tokens_info_pointer, token)

        else:
            with open(f'../data/index/tokens_info_others_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())

            tokens_info_pointer = f'../data/index/tokens_info_others.txt'
            token_info = self.binary_search_token_info(num_tokens, tokens_info_pointer, token)

        return token_info

    def get_wild_card_info(self, perm_token, num_results=5):
        valid_list = [chr(i) for i in range(97, 123)] + [str(i) for i in range(0, 10)] + ['$']
        if perm_token[0] in valid_list:
            with open(f'../data/wild-card/output/perm_token_info_{perm_token[0]}_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())
            tokens_info_pointer = f'../data/wild-card/output/perm_token_info_{perm_token[0]}.txt'
            token_info = self.binary_search_wild_card_info(num_tokens, tokens_info_pointer, perm_token,
                                                           num_results=num_results)

        else:
            token_info = None

        return token_info


'''
This class takes query as input and returns the corresponding postings along with theis fields
'''
class QueryResults():

    def __init__(self, file_traverser):

        self.file_traverser = file_traverser

    def deal_with_wird_card(self, token):
        """WILD CARD
        Only support:
            - one '*' e.g. X*, *X, X*Y
            - two '*'s: e.g. *X* and X*Y*Z
        """
        pattern1 = re.compile('^\*[0-9a-z]+\*$')  # *X*
        pattern2 = re.compile('^[0-9a-z]+\*[0-9a-z]+\*[0-9a-z]+$')  # X*Y*Z
        n = 10
        num_results = n
        count = token.count('*')
        if not count or count >= 3:
            return []
        if count == 1:
            # X* -> X*$
            new_token = token + '$'
        else:
            if re.match(pattern1, token):
                # *X* -> X*
                new_token = re.findall(r'\*[0-9a-z]+\*', token)[0][1:]
            elif re.match(pattern2, token):
                # X*Y*Z -> X*Z$
                Y = re.findall(r'\*[0-9a-z]+\*', token)[0][1:-1]
                new_token = re.findall(r'^[0-9a-z]+\*', token)[0] + re.findall(r'\*[0-9a-z]+$', token)[0][1:]
                new_token = new_token + '$'
                num_results = None
            else:
                return []

        pos = new_token.find('*')
        perm_token = new_token[pos + 1:] + new_token[: pos]
        postings = self.file_traverser.get_wild_card_info(perm_token, num_results=num_results)
        if re.match(pattern2, token):
            postings = list(filter(lambda x: Y in x[0], postings))
            # postings.sort(key=lambda x: x[2], reverse=True)
            postings = postings[:n]
        # print([token[0] for token in tokens])
        return postings

    def simple_query_wild_card(self, preprocessed_query):

        final_results = []
        page_freq, page_postings = {}, defaultdict(dict)

        all_tokens, all_cand_tokens = [], []
        for token in preprocessed_query:
            if '*' in token:
                token_infos = self.deal_with_wird_card(token)
                # token, file_num, freq, ...
                all_cand_tokens = token_infos
            else:
                token_info = self.file_traverser.get_token_info(token)
                if token_info:
                    all_tokens.append([token, token_info])

        for token, token_info in all_tokens:
            file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
            line_map = {
                'title': title_line,
                'body': body_line,
                'category': category_line,
                'infobox': infobox_line,
                'link': link_line,
                'reference': reference_line
            }
            page_freq[token] = freq
            for field_name, line_num in line_map.items():

                if line_num != '':
                    posting = self.file_traverser.search_field_file(field_name, file_num, line_num)

                    # page_freq[token] = len(posting.split(';'))
                    page_postings[token][field_name] = posting

        if not all_cand_tokens:  # not wild card
            final_results.append([page_freq, page_postings])
            return final_results

        for cand_tokens in all_cand_tokens:
            cand_page_freq, cand_page_postings = page_freq.copy(), page_postings.copy()
            token, *token_info = cand_tokens
            file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
            line_map = {
                'title': title_line,
                'body': body_line,
                'category': category_line,
                'infobox': infobox_line,
                'link': link_line,
                'reference': reference_line
            }
            cand_page_freq[token] = freq
            for field_name, line_num in line_map.items():

                if line_num != '':
                    posting = self.file_traverser.search_field_file(field_name, file_num, line_num)

                    # page_freq[token] = len(posting.split(';'))
                    cand_page_postings[token][field_name] = posting
            final_results.append([cand_page_freq, cand_page_postings])
        return final_results

    def field_query_wild_card(self, preprocessed_query):
        """
        preprocessed_query: [[<field>, <token>], ...]
        """
        final_results = []
        page_freq, page_postings = {}, defaultdict(dict)

        all_tokens, all_cand_tokens = [], []
        for field, token in preprocessed_query:
            if '*' in token:
                token_infos = self.deal_with_wird_card(token)
                # token, file_num, freq, ...
                all_cand_tokens.extend([[field, token_info] for token_info in token_infos])
            # [c, [posting1, posting2]]
            else:
                token_info = self.file_traverser.get_token_info(token)
                if token_info:
                    all_tokens.append([field, token, token_info])
        field_map = {
            't': 'title',
            'b': 'body',
            'c': 'category',
            'i': 'infobox',
            'l': 'link',
            'r': 'reference'
        }
        for field, token, token_info in all_tokens:
            file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
            line_map = {
                'title': title_line,
                'body': body_line,
                'category': category_line,
                'infobox': infobox_line,
                'link': link_line,
                'reference': reference_line
            }

            field_name = field_map[field]
            line_num = line_map[field_name]

            posting = self.file_traverser.search_field_file(field_name, file_num, line_num)
            # page_freq[token] = len(posting)
            page_freq[token] = freq
            page_postings[token][field_name] = posting

        if not all_cand_tokens:
            final_results.append([page_freq, page_postings])
            return final_results

        for field, cand_tokens in all_cand_tokens:
            cand_page_freq, cand_page_postings = page_freq.copy(), page_postings.copy()
            token, *token_info = cand_tokens

            file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
            line_map = {
                'title': title_line,
                'body': body_line,
                'category': category_line,
                'infobox': infobox_line,
                'link': link_line,
                'reference': reference_line
            }
            field_name = field_map[field]
            line_num = line_map[field_name]

            posting = self.file_traverser.search_field_file(field_name, file_num, line_num)
            cand_page_freq[token] = freq
            cand_page_postings[token][field_name] = posting
            final_results.append([cand_page_freq, cand_page_postings])
        return final_results

    def simple_query(self, preprocessed_query):

        page_freq, page_postings = {}, defaultdict(dict)

        for token in preprocessed_query:
            token_info = self.file_traverser.get_token_info(token)

            if token_info:
                file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
                line_map = {
                    'title' : title_line, 'body' : body_line, 'category' : category_line, 'infobox' : infobox_line, 'link' : link_line, 'reference' : reference_line
                }

                for field_name, line_num in line_map.items():
                    if line_num!='':
                        posting = self.file_traverser.search_field_file(field_name, file_num, line_num)
                        page_freq[token] = len(posting.split(';'))
                        page_postings[token][field_name] = posting


        return page_freq, page_postings


    def field_query(self, preprocessed_query):

        page_freq, page_postings = {}, defaultdict(dict)

        for field, token in preprocessed_query:
            token_info = self.file_traverser.get_token_info(token)

            if token_info:
                file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
                line_map = {
                    'title':title_line, 'body':body_line, 'category':category_line, 'infobox':infobox_line, 'link':link_line, 'reference':reference_line
                }
                field_map = {
                    't':'title', 'b':'body', 'c':'category', 'i':'infobox', 'l':'link', 'r':'reference'
                }

                field_name = field_map[field]
                line_num = line_map[field_name]

                posting = self.file_traverser.search_field_file(field_name, file_num, line_num)
                page_freq[token] = len(posting)
                page_postings[token][field_name] = posting

        return page_freq, page_postings


'''
This class runs the above functions to implement search and ranking and returns the required results.
'''
class RunQuery():

    def __init__(self, text_pre_processor, file_traverser, ranker, query_results):

        self.file_traverser = file_traverser
        self.text_pre_processor = text_pre_processor
        self.ranker = ranker
        self.query_results = query_results

    def identify_query_type(self, query):

        field_replace_map = {
            ' t:':';t:',
            ' b:':';b:',
            ' c:':';c:',
            ' i:':';i:',
            ' l:':';l:',
            ' r:':';r:',
        }

        if ('t:' in query or 'b:' in query or 'c:' in query or 'i:' in query or 'l:' in query or 'r:' in query) and query[0:2] not in ['t:', 'b:', 'i:', 'c:', 'r:', 'l:']:

            for k, v in field_replace_map.items():
                if k in query:
                    query = query.replace(k, v)

            query = query.lstrip(';')

            return query.split(';')[0], query.split(';')[1:]

        elif 't:' in query or 'b:' in query or 'c:' in query or 'i:' in query or 'l:' in query or 'r:' in query:

            for k, v in field_replace_map.items():
                if k in query:
                    query = query.replace(k, v)

            query = query.lstrip(';')

            return query.split(';'), None

        else:
            return query, None

    def return_query_results(self, query, query_type, method='weighted_field_tf_idf'):
        if query_type == 'field':
            # input: [c:apple, t:pear orange]
            wild_card_token = ''
            preprocessed_query = []
            for qry in query:
                field, tokens = qry.split(':')
                new_tokens = []
                for token in tokens.split(' '):
                    if '*' in token:
                        wild_card_token = token
                    else:
                        new_tokens.append(token)
                preprocessed_query.append([
                    field, self.text_pre_processor.preprocess_text(' '.join(new_tokens))])
                if wild_card_token:
                    preprocessed_query[-1][1].append(wild_card_token)
        # output: [[c, [apple]], [t, [pear,orange]]]
        else:
            # input: I like to eat
            # preprocessed_query = self.text_pre_processor.preprocess_text(query)
            wild_card_token = ''
            new_query = []
            for token in query.split(' '):
                if '*' in token:
                    wild_card_token = token
                else:
                    new_query.append(token)
            preprocessed_query = self.text_pre_processor.preprocess_text(' '.join(new_query))
            if wild_card_token:
                preprocessed_query.append(wild_card_token)
        # output: [like, eat]

        if query_type == 'field':
            preprocessed_query_final = []
            for field, words in preprocessed_query:
                for word in words:
                    preprocessed_query_final.append([field, word])
            final_results = self.query_results.field_query_wild_card(preprocessed_query_final)
        else:
            final_results = self.query_results.simple_query_wild_card(preprocessed_query)

        ranked_results, relevant_tokens = {}, set()
        for page_freq, page_postings in final_results:
            for token in page_freq.keys():
                relevant_tokens.add(token)

            tmp_ranked_results = self.ranker.rank(
                method=method,
                page_freq=page_freq,
                page_postings=page_postings
            )
            for doc_id, score in tmp_ranked_results.items():
                if doc_id not in ranked_results or ranked_results[doc_id] < score:
                    ranked_results[doc_id] = score

        return ranked_results, relevant_tokens

    def take_input_from_file(self, file_name, num_results):
        results_file = file_name.split('.txt')[0]
        with open(file_name, 'r') as f:
            fp = open(results_file + '_op.txt', 'w')
            for i, query in enumerate(f):
                s = time.time()
                query = query.strip()
                query = Checker.query_spell_check(query)
                print(f'After spell correction:- {query}')
                query1, query2 = self.identify_query_type(query)

                if query2:
                    ranked_results1, relevant_tokens1 = self.return_query_results(query1, 'simple')

                    ranked_results2, relevant_tokens2 = self.return_query_results(query2, 'field')

                    relevant_tokens = relevant_tokens1 | relevant_tokens2

                    ranked_results = Counter(ranked_results1) + Counter(ranked_results2)
                    results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                    results = results[:num_results]

                    if results:
                        for id, _ in results:
                            title = self.file_traverser.title_search(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching Doc found')
                        fp.write('\n')

                elif type(query1) == type([]):

                    ranked_results, relevant_tokens = self.return_query_results(query1, 'field')

                    results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                    results = results[:num_results]

                    if results:
                        for id, _ in results:
                            title = self.file_traverser.title_search(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching Doc found')
                        fp.write('\n')

                else:
                    ranked_results, relevant_tokens = self.return_query_results(query1, 'simple')

                    results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                    results = results[:num_results]

                    if results:
                        for id, _ in results:
                            title = self.file_traverser.title_search(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching Doc found')
                        fp.write('\n')

                e = time.time()
                print('Relevant tokens')
                print(relevant_tokens)
                fp.write('Finished in ' + str(e-s) + ' seconds')
                fp.write('\n\n')

                print('Done query', i+1)

            fp.close()

        print('Done writing results')

    def take_input_from_user(self, num_results):

        start = time.time()

        while True:
            query = input('Enter Query:- ')
            s = time.time()

            query = query.strip()
            query = Checker.query_spell_check(query)
            print(f'After spell correction:- {query}')
            query1, query2 = self.identify_query_type(query)
            print(query1, query2)

            if query2:
                ranked_results1, relevant_tokens1 = self.return_query_results(query1, 'simple')

                ranked_results2, relevant_tokens2 = self.return_query_results(query2, 'field')

                relevant_tokens = relevant_tokens1 | relevant_tokens2

                ranked_results = Counter(ranked_results1) + Counter(ranked_results2)
                results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                results = results[:num_results]

                for id, _ in results:
                    title= self.file_traverser.title_search(id)
                    print(id+',', title)

            elif type(query1)==type([]):

                ranked_results, relevant_tokens = self.return_query_results(query1, 'field')

                results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                results = results[:num_results]

                for id, _ in results:
                    title= self.file_traverser.title_search(id)
                    print(id+',', title)

            else:
                ranked_results, relevant_tokens = self.return_query_results(query1, 'simple')

                results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                results = results[:num_results]

                for id, _ in results:
                    title= self.file_traverser.title_search(id)
                    print(id+',', title)

            e = time.time()
            print('Relevant tokens')
            print(relevant_tokens)
            print('Finished in', e-s, 'seconds')
            print()

    def query_api(self, query, method):

        start = time.time()

        query = query.strip()

        # category specific
        retain_docid = CategoryFilter().filter_pages(query)

        if retain_docid is not None:
            query = query.split(" | ")[0].strip()

        ori_query = query
        query = Checker.query_spell_check(query)
        if query == ori_query:
            corrected_query = None
        else:
            corrected_query = query
        # print(f'After spell correction:- {query}')

        query1, query2 = self.identify_query_type(query)

        if query2:
            ranked_results1, relevant_tokens1 = self.return_query_results(query1, 'simple', method)

            ranked_results2, relevant_tokens2 = self.return_query_results(query2, 'field', method)

            relevant_tokens = relevant_tokens1 | relevant_tokens2

            ranked_results = Counter(ranked_results1) + Counter(ranked_results2)

        elif type(query1)==type([]):
            ranked_results, relevant_tokens = self.return_query_results(query1, 'field', method)
        else:
            ranked_results, relevant_tokens = self.return_query_results(query1, 'simple', method)

        # filter
        if retain_docid is not None:
            retain_docid = {str(docid): docid for docid in retain_docid}  # to speed up
            tmp_ranked_results = {}
            for docid, score in ranked_results.items():
                if docid in retain_docid:
                    tmp_ranked_results[docid] = score
            ranked_results = tmp_ranked_results

        print('Finished in', time.time() - start, 'seconds')
        print()

        return {
            'ranked_results': ranked_results,
            'corrected_query': corrected_query,
            'relevant_tokens': relevant_tokens
        }


'''
This is the main function which does entire searching task.
'''
if __name__=='__main__':
    start = time.time()

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--filename', action='store', type=str)
    arg_parser.add_argument('--num_results', action='store', default=10, type=int)

    args = arg_parser.parse_args()

    file_name = args.filename
    num_results = args.num_results

    print('Loading search engine ')
    stop_words = (set(stopwords.words("english")))
    html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
    stemmer = Stemmer('english')

    with open('../data/index/num_pages.txt', 'r') as f:
        num_pages = float(f.readline().strip())

    text_pre_processor = TextPreProcessor(html_tags, stemmer, stop_words)
    file_traverser = FileTraverser()
    ranker = Ranker(num_pages)
    query_results = QueryResults(file_traverser)
    run_query = RunQuery(text_pre_processor, file_traverser, ranker, query_results)

    temp = linecache.getline('../data/index/id_title_map.txt', 0)

    print('Loaded in', time.time() - start, 'seconds')

    print('Starting Querying')

    start = time.time()

    if file_name is not None:
        run_query.take_input_from_file(file_name, num_results)
    else:
        run_query.take_input_from_user(num_results)
    print('Done querying in', time.time() - start, 'seconds')
