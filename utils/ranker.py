"""
Search ranker.
"""
import math
import numpy as np
from collections import defaultdict


class Ranker(object):
    def __init__(self, num_pages):
        self.num_pages = num_pages

    @staticmethod
    def _log_tfidf_score(tf, df, N):
        idf = math.log(N / df)
        return (1 + math.log(tf)) * idf

    @staticmethod
    def _bm25_score(tf, df, N, doc_len, avg_doc_len, k1=2, b=0.75):
        K = k1 * (1 - b + b * doc_len / avg_doc_len)
        idf = math.log((N - df + 0.5) / (df + 0.5))
        return idf * (tf * (k1 + 1)) / (tf + K)

    def _rank(
            self,
            page_freq,
            page_postings,
            weightage_dict=None,
            use_cosine=False,
            use_cate_generality=False,
            score_func='tf_idf'
    ):
        """
        TF-IDF ranking with weights assigned on different fields.
        Currently support 3 out of 5 rank methods:
        (1) Weighted field TF-IDF ranking
        (2) Field-specific TF-IDF ranking
        (3) TF-IDF ranking with cosine similarity
        (4) BM25
        (5) Category-field TF-IDF ranking w/ category generality in consideration.
        """
        if weightage_dict is None:
            weightage_dict = {
                'title': 1.0,
                'body': 0.6,
                'category': 0.4,
                'infobox': 0.75,
                'link': 0.20,
                'reference': 0.25
            }

        # load document length for BM25
        if score_func == 'bm25':
            doc_len_dict, avg_doc_len = dict(), 0
            with open('../data/index/num_page_tokens.txt', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    doc_id, doc_len = line.split('-')
                    doc_len = int(doc_len)
                    doc_len_dict[doc_id] = doc_len
                    avg_doc_len += doc_len
                avg_doc_len /= len(doc_len_dict)

        result = dict()

        # calculate rank score
        for token, field_post_dict in page_postings.items():
            for field, postings in field_post_dict.items():
                weightage = weightage_dict[field]
                if len(postings) > 0:
                    for post in postings.split(';'):
                        id, post = post.split(':')
                        # score func
                        if score_func == 'tf_idf':
                            score = weightage * Ranker._log_tfidf_score(
                                int(post),
                                int(page_freq[token]),
                                self.num_pages
                            )
                        elif score_func == 'bm25':
                            score = weightage * Ranker._bm25_score(
                                int(post),
                                int(page_freq[token]),
                                self.num_pages,
                                doc_len=doc_len_dict[id],
                                avg_doc_len=avg_doc_len,
                            )

                        # use cosine similarity or sum of score
                        if use_cosine:
                            if id not in result:
                                result[id] = defaultdict(float)
                            vec = result[id]
                            vec[token] += score
                        else:
                            if id not in result:
                                result[id] = 0.
                            result[id] += score

        # aggregate vec if use cosine similarity
        if use_cosine:
            new_result = dict()
            for id, vec in result.items():
                vec = list(vec.values())
                vec = np.array(vec)
                new_result[id] = np.sqrt(np.sum(vec ** 2))
            result = new_result

        # add category score if use cate generality
        if use_cate_generality:
            cate_to_root_dist = dict()
            with open('../data/index/id_generality_map.txt', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    doc_id, dist = line.split('-')
                    dist = int(dist)
                    cate_to_root_dist[doc_id] = dist
            for id in result.keys():
                dist = cate_to_root_dist.get(id, 100)
                if dist == 100:
                    result[id] = 0.
                else:
                    result[id] *= (1 / dist)
        return result

    def rank(
            self,
            method,
            page_freq,
            page_postings,
            weightage_dict=None,
    ):
        """
        A wrapper for ranking.
        """
        if method == 'weighted_field_tf_idf':
            return self._rank(
                page_freq,
                page_postings,
                weightage_dict,
                score_func='tf_idf'
            )
        elif method == 'cosine_similarity_tf_idf':
            return self._rank(
                page_freq,
                page_postings,
                weightage_dict,
                use_cosine=True,
                score_func='tf_idf'
            )
        elif method == 'bm25':
            return self._rank(
                page_freq,
                page_postings,
                weightage_dict,
                score_func='bm25'
            )
        elif method == 'category_generality':
            return self._rank(
                page_freq,
                page_postings,
                weightage_dict,
                use_cate_generality=True,
                score_func='tf_idf'
            )
        else:
            raise ValueError(f'Rank method {method} is not supported.')
