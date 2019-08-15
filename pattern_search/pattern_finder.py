'''
Contributors: Olga Zamaraeva, Alexis Palmer
olzama@uw.edu

For the Pittsburgh workshop on Technology for Language Documentation and Revitalization
(August 12-16, 2019)

Scenario: Teacher identifies a pattern of pedagogical interest, such as a word or a phrase.
This program should find uses of that pattern in a given corpus.

I will start this program as a straightforward pattern-matching function but it can later
evolve into something more complex (e.g.: allomorphy, complex syntactic phenomena which manifest themselves
in a variety of ways, etc.)
'''

import argparse
import textwrap
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


# REPORT FORMATTING PARAMETERS ################################################

MAX_LINE_WIDTH = 120
RESULT_WIDTH   = 13 # Reserved for 'PARTIAL MATCH'
MATCH          = 'MATCH'
PARTIAL_MATCH  = 'PARTIAL MATCH' # to use with editdistance or something similar
NO_MATCH       = 'NO MATCH'

# EXCEPTIONS ##################################################################

class PatternFinderError(Exception):
    """Raised when a the program fails for any reason."""

# VALIDATION OF ARGUMENTS

def validate_arguments(args,parser):
    success = True
    if not args.string:
        print('Please provide the string which contains the highlighted patterns.')
        success = False
    if not args.indices:
        print('Please provide the indices of the patterns highlighted in the string.')
        success = False
    if not args.corpus:
        print('Please provide a corpus to search in.')
        success = False
    if args.string == '*':
        print('Don\'t do that (use * as your pattern)' )
        success = False
    if not (args.words or args.morphemes or args.discont):
        print('Default: Treating the entire sentence as pattern.')
    if not success:
        print('\n')
        parser.print_help()
        exit(1)

# PREPROCESSING OF DATA

def get_indices(args):
    indices = []
    for index_pair in args.indices.split(','):
        split = index_pair.split('-')
        start = int(split[0])
        end = int(split[1])
        indices.append((start, end))
    return indices

def normalize(s):
    norm_s = s.lower().strip('\n')
    return norm_s

# MATCHING FUNCTIONS ##########################################################

'''
The pattern to match is the entire sentence.
'''
def get_sentences_pattern(string, indices):
    return string[indices[0]:indices[1]+1]

'''
The pattern to match is one or more contiguous words.
'''
def get_words_pattern(string, indices):
    substr = string[indices[0]:indices[1]+1]
    pattern = r'\b'+substr+r'\b' # \b is word boundary
    return pattern

'''
The pattern to match is one or more contiguous morphemes.
'''
def get_morphemes_pattern(string, indices):
    substr = string[indices[0]:indices[1]+1]
    pattern = r'\B'+substr+'|'+substr+r'\B'
    return pattern

'''
The pattern to match is a discontinuous span.
'''
def get_discont_span_pattern(strings, list_of_index_pairs):
    pattern = strings[0]
    return pattern

def simpleMatch(corpus, pattern):
    results = []
    regex = re.compile(pattern,re.I)
    for ln in corpus:
        norm_ln = normalize(ln)
        matches = list(re.finditer(regex, norm_ln))
        if matches:
            match_spans = []
            for m in matches:
                match_spans.append(m.span())
            results.append((norm_ln,match_spans))
            print(norm_ln)
    return results


def fuzzyMatch(corpus, pattern):
    matches = []
    for ln in corpus:
        norm_ln = normalize(ln)
        # ratio = fuzz.ratio(string, norm_ln)
        partialRatio = fuzz.partial_ratio(pattern, norm_ln)
        tokenSetRatio = fuzz.token_set_ratio(pattern, norm_ln)

        if partialRatio >= 65:
            matches.append(ln)
            print(partialRatio, norm_ln.strip('\n'))

        elif tokenSetRatio >= 65:
            print("----------- token set ratio ------------")
            matches.append(ln)
            print(tokenSetRatio, norm_ln.strip('\n'))
            
    return matches

def tryProcess(corpus, pattern):
    ''' process module from fuzzywuzzy -seems to score differently from partialRatio & tokenSetRatio '''
    print(len(corpus))
    matches = process.extract(pattern, corpus)
    print(matches)


# MAIN FUNCTIONS ##############################################################
'''
Return a list of sentences where a match was found.
'''
def main(args):
    with open(args.corpus,'r') as f:
        corpus = f.readlines()
    indices = get_indices(args)
    s = normalize(args.string)
    if args.words:
        p = get_words_pattern(s,indices[0])
    elif args.morphemes:
        p = get_morphemes_pattern(s,indices[0])
    elif args.discont:
        p = get_discont_span_pattern(s,indices)
    else:
        p = get_sentences_pattern(s,indices[0])
    if args.fuzzy:
        matches = fuzzyMatch(corpus, p)
    else:
        matches = simpleMatch(corpus, p)
#    print("testing process function from fuzzywuzzy")
#    tryProcess(corpus, s)
    # matches = []
    # for ln in corpus:
    #     norm_ln = normalize(ln)
    #     match = re.search(s,norm_ln)
    #     if match:
    #         matches.append(ln)
    #         print(norm_ln.strip('\n'))
    if len(matches) == 0:
        print(NO_MATCH)
    if args.output:
        with open(args.output, 'w') as f:
            for m in matches:
                f.write(m[0])
    return matches

# SCRIPT ENTRYPOINT ###########################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Scenario: Teacher identifies a pattern of pedagogical interest,
        such as a word or a phrase.
        This program should find uses of that pattern in a given corpus.
        '''),
        epilog=textwrap.dedent('''\
        Examples:
            %(prog)s STRING CORPUS   # take a string and return matches from the corpus
        '''))
    parser.add_argument('-s', '--string',
                        help='string in which the pattern was highlighted')
    parser.add_argument('-i', '--indices',
                        help='indices of highlighted span(s)')
    parser.add_argument('-w', '--words', action='store_true',
                        help='search for one of more full contiguous words')
    parser.add_argument('-m', '--morphemes', action='store_true',
                        help='search for one or more contiguous morphemes')
    parser.add_argument('-d', '--discont', action='store_true',
                        help='search for a discontinuous span')
    parser.add_argument('-l', '--sentence', action='store_false',
                        help='search for an entire sentence')
    parser.add_argument('-c', '--corpus',
                        help='corpus to find matches in')
    parser.add_argument('-o', '--output',
                        help='path to the output file')
    parser.add_argument('-f', '--fuzzy', action='store_true',
                          help='select partial matches')
    args = parser.parse_args()
    validate_arguments(args,parser)
    main(args)
    
