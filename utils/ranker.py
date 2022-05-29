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
    def _log_tfidf_score(tf, idf, N):
        return (1 + math.log(tf)) * math.log(N / idf)

    @staticmethod
    def _get_cate_generality(doc_id):
        # TODO
        return 1

    @staticmethod
    def _get_doc_num_term(doc_id):
        # TODO
        return 1000

    def tfidf_rank(self, page_freq, page_postings, weightage_dict=None, use_cosine=True, use_cate_generality=True):
        """
        TF-IDF ranking with weights assigned on different fields.
        Currently support 3 out of 5 rank methods:
        (1) Weighted field TF-IDF ranking
        (2) Field-specific TF-IDF ranking
        (3) [in construction] TF-IDF ranking with cosine similarity
        (4) [in construction] Category-field TF-IDF ranking w/ category generality in consideration.
        (5) [in construction]
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

        result = dict()

        # calculate tf-idf
        for token, field_post_dict in page_postings.items():
            for field, postings in field_post_dict.items():
                weightage = weightage_dict[field]
                if len(postings) > 0:
                    for post in postings.split(';'):
                        id, post = post.split(':')
                        score = weightage * Ranker._log_tfidf_score(int(post), int(page_freq[token]), self.num_pages)
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
                new_result[id] = np.sqrt(np.sum(vec ** 2) / Ranker._get_doc_num_term(id))
            result = new_result

        # add category score if use cate generality
        if use_cate_generality:
            result[id] += Ranker._get_cate_generality(id)

        return result