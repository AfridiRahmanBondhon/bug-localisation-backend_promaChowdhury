import glob
import os.path
from collections import OrderedDict

import javalang
import pygments
from pygments.lexers import JavaLexer
from pygments.token import Token
import re
import inflection
import nltk
from nltk.stem.porter import PorterStemmer
import string
from assets import java_keywords, stop_words
from github import Github
import json


def extract_stack_traces(description):
    regex = r"(.*?)\((.*?)\)"

    matches = re.findall(regex, description)
    signs = [".java", "Unknown Source", "Native Method"]
    st_candid = []

    if matches:
        for match in matches:
            st_candid.append(match)
        st = [x for x in st_candid if any(s in x[1] for s in signs)]
        return st
    else:
        return []


def get_summ_description(repo_name, repo_owner, issue_number):
    github_token = "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"
    g = Github(github_token)

    repo = g.get_repo(f"{repo_owner}/{repo_name}")

    issue = repo.get_issue(issue_number)
    description = issue.body
    summary = issue.title
    return summary, description


def tokenize(entity):
    t_summary = nltk.wordpunct_tokenize(entity)
    return t_summary


def pos_tagging(entity):
    summ_tok = nltk.word_tokenize(entity)
    sum_pos = nltk.pos_tag(summ_tok)

    res = [token for token, pos in sum_pos if "NN" in pos or "VB" in pos]
    # desc_pos = nltk.pos_tag(t_description)
    return res


def _split_camelcase(tokens):
    returning_tokens = tokens[:]

    for token in tokens:
        split_tokens = re.split(rf"[{string.punctuation}]+", token)

        if len(split_tokens) > 1:
            returning_tokens.remove(token)
            for st in split_tokens:
                camel_split = inflection.underscore(st).split("_")
                if len(camel_split) > 1:
                    returning_tokens.append(st)
                    returning_tokens += camel_split
                else:
                    returning_tokens.append(st)
        else:
            camel_split = inflection.underscore(token).split("_")
            if len(camel_split) > 1:
                returning_tokens += camel_split

    return returning_tokens


def split_camelcase(entity):
    return _split_camelcase(entity)


def remove_stopwords(entity):
    return [token for token in entity if token not in stop_words]


def remove_java_keywords(entity):
    return [token for token in entity if token not in java_keywords]


def stem(entity):
    # Stemmer instance
    stemmer = PorterStemmer()
    res = dict(
        zip(
            ["stemmed", "unstemmed"],
            [[stemmer.stem(token) for token in entity], entity],
        )
    )
    return res


def normalize(entity):
    punctnum_table = str.maketrans(
        {c: None for c in string.punctuation + string.digits}
    )
    summary_punctnum_rem = [token.translate(punctnum_table) for token in entity]
    return summary_punctnum_rem


def process_bug_pos_taggers(entity):
    pos_desc = pos_tagging(entity)
    # token_desc = tokenize(pos_desc)
    cc_desc = split_camelcase(pos_desc)
    norm_desc = normalize(cc_desc)
    rem_stop = remove_stopwords(norm_desc)
    rem_java = remove_java_keywords(rem_stop)
    res = stem(rem_java)
    return res


def process_bug_entity(entity):
    token_desc = tokenize(entity)
    cc_desc = split_camelcase(token_desc)
    norm_desc = normalize(cc_desc)
    rem_stop = remove_stopwords(norm_desc)
    rem_java = remove_java_keywords(rem_stop)
    res = stem(rem_java)

    return res


def process_bug_report(repo_name, repo_owner, issue_number):
    summary, description = get_summ_description(
        repo_name=repo_name, repo_owner=repo_owner, issue_number=issue_number
    )

    print(summary,description)
    real_summary = summary
    stack_trace = extract_stack_traces(description)
    summary_processed = process_bug_entity(summary)
    description_processed = process_bug_entity(description)
    pos_summary = process_bug_pos_taggers(summary)
    pos_description = process_bug_pos_taggers(description)

    dic = {
        "real_summary":summary,
        "summary": summary_processed,
        "stack_trace": stack_trace,
        "description": description_processed,
        "pos_tagged_summary": pos_summary,
        "pos_tagged_description": pos_description,
    }
    
    out_file = open("report.json", "w")

    
    json.dump(dic, out_file, indent=6)

    out_file.close()
