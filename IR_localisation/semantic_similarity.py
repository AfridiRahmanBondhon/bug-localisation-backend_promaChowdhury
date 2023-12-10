import spacy
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import json


def calculate_similarity(src_files, bug_reports):
    # Loading word vectors
    nlp = spacy.load("en_core_web_lg")

    src_docs = [
        nlp(
            " ".join(
                src["file_name"]["unstemmed"]
                + src["class_names"]["unstemmed"]
                + src["attributes"]["unstemmed"]
                + src["comments"]["unstemmed"]
                + src["method_names"]["unstemmed"]
            )
        )
        for src in src_files.values()
    ]

    min_max_scaler = MinMaxScaler()

    all_simis = []
    bug_reports = {"bug": bug_reports}
    for report in bug_reports.values():
        report_doc = nlp(
            " ".join(
                report["summary"]["unstemmed"]
                + report["pos_tagged_description"]["unstemmed"]
            )
        )
        scores = []
        for src_doc in src_docs:
            simi = report_doc.similarity(src_doc)
            scores.append(simi)

        scores = np.array([float(count) for count in scores]).reshape(-1, 1)
        normalized_scores = np.concatenate(min_max_scaler.fit_transform(scores))

        all_simis.append(normalized_scores.tolist())

    return all_simis


def semantic_similarity():
    with open("report.json", "r") as json_file:
        bug_reports = json.load(json_file)
    with open("source.json", "r") as json_file:
        src_files = json.load(json_file)
    all_simis = calculate_similarity(src_files, bug_reports)

    with open("semantic_similarity.json", "w") as file:
        json.dump(all_simis[0], file)
