"""
Query spell checker.
"""
from nltk.metrics.distance import jaccard_distance, edit_distance
from nltk.util import ngrams
from nltk.corpus import words


class Checker(object):
    def __init__(self):
        pass

    @staticmethod
    def _jaccard_distance_closest(word):
        """
        Find the closest jaccard distance word for spell correction.
        """
        correct_words = words.words()
        candi_list = [(jaccard_distance(set(ngrams(word, 2)),
                                  set(ngrams(w, 2))), w)
                for w in correct_words if w[0] == word[0]]
        return sorted(candi_list, key=lambda val: val[0])[0][1]

    @staticmethod
    def _edit_distance_closest(word):
        """
        Find the closest edit distance word for spell correction.
        """
        correct_words = words.words()
        candi_list = [(edit_distance(word, w), w) for w in correct_words if w[0] == word[0]]
        return sorted(candi_list, key=lambda val: val[0])[0][1]

    @staticmethod
    def word_spell_check(word, metric='jaccard_dist'):
        """
        Check the word spelling and return the corrected word.
        """
        if '*' in word:
            return word

        if metric == 'jaccard_dist':
            return Checker._jaccard_distance_closest(word)
        elif metric == 'edit_dist':
            return Checker._edit_distance_closest(word)
        else:
            raise ValueError(f"Metric {metric} for spelling check is not supported.")

    @staticmethod
    def query_spell_check(query):
        words = query.split(':')
        corrected_query = ' '.join([Checker.word_spell_check(w) for w in words[-1].split()])
        if len(words) > 1:
            field = words[0]
            return field + ': ' + corrected_query
        else:
            return corrected_query


if __name__ == '__main__':
    correct_words = words.words()
    # list of incorrect spellings
    # that need to be corrected
    incorrect_words = ['pwople', 'happpy', 'azmaing', 'intelliengt', 'rodwer']

    print(incorrect_words)
    print('After correction->')

    # loop for finding correct spellings
    # based on jaccard distance
    # and printing the correct word
    print('\njaccard distance')
    for word in incorrect_words:
        print(Checker.word_spell_check(word, metric='jaccard_dist'))
    print('\nedit distance')
    for word in incorrect_words:
        print(Checker.word_spell_check(word, metric='edit_dist'))
