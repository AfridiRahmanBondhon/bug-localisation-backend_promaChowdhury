import json
import operator
import pickle

import numpy as np
from scipy import optimize
from vsm_similarity import vsm_similarity
from stack_trace import stack_trace
from semantic_similarity import semantic_similarity
from token_matching import token_matching
from process_bug_report import process_bug_report
from process_src import process_src
import concurrent


def main():
    with open("report.json", "r") as json_file:
        bug_reports = json.load(json_file)
    with open("source.json", "r") as json_file:
        src_files = json.load(json_file)
    with open("token_matching.json", "r") as file:
        token_matching_score = json.load(file)
    with open("vsm_similarity.json", "r") as file:
        vsm_similarity_score = json.load(file)
    with open("stack_trace.json", "r") as file:
        stack_trace_score = json.load(file)
    with open("semantic_similarity.json", "r") as file:
        semantic_similarity_score = json.load(file)

    files = list(src_files.keys())
    score_dict = []

    for i in range(len(files)):
        score = (
            0.2 * token_matching_score[i]
            + 0.2 * vsm_similarity_score[i]
            + 0.5 * semantic_similarity_score[i]
            + 10 * stack_trace_score[i]
        )
        score_dict.append({"file": files[i], "score": score})
    sorted_array = sorted(score_dict, key=lambda item: item["score"], reverse=True)
    return sorted_array


def evaluate(repo_name, repo_owner, issue_number):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_bug_report = executor.submit(
            process_bug_report, repo_name, repo_owner, issue_number
        )
        future_src = executor.submit(process_src)

        concurrent.futures.wait([future_bug_report, future_src])

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(stack_trace),
            executor.submit(token_matching),
            executor.submit(vsm_similarity),
            executor.submit(semantic_similarity),
        ]

        concurrent.futures.wait(futures)

    return main()


# 1864 //1843
