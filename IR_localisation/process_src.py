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
import json


def src_parser(src_folder):
    """Parse source code directory of a program and collect
    its java files.
    """

    src_addresses = glob.glob(str(src_folder) + "/**/*.java", recursive=True)

    java_lexer = JavaLexer()

    src_files = {}

    for src_file in src_addresses:
        with open(src_file, encoding="cp1256") as file:
            src = file.read()

        # Placeholder for different parts of a source file
        comments = ""
        class_names = []
        attributes = []
        method_names = []
        variables = []

        # Source parsing
        parse_tree = None
        try:
            parse_tree = javalang.parse.parse(src)
            for path, node in parse_tree.filter(javalang.tree.VariableDeclarator):
                if isinstance(path[-2], javalang.tree.FieldDeclaration):
                    attributes.append(node.name)
                elif isinstance(path[-2], javalang.tree.VariableDeclaration):
                    variables.append(node.name)
        except:
            pass

        lexed_src = pygments.lex(src, java_lexer)

        for i, token in enumerate(lexed_src):
            if token[0] in Token.Comment:
                if i == 0 and token[0] is Token.Comment.Multiline:
                    src = src[src.index(token[1]) + len(token[1]) :]
                    continue
                comments += token[1]
            elif token[0] is Token.Name.Class:
                class_names.append(token[1])
            elif token[0] is Token.Name.Function:
                method_names.append(token[1])

        if parse_tree and parse_tree.package:
            package_name = parse_tree.package.name
        else:
            package_name = None

            # If source file has package declaration
        if package_name:
            src_id = package_name + "." + os.path.basename(src_file)
        else:
            src_id = os.path.basename(src_file)

        src_files[src_id] = {
            "all_content": src,
            "comments": comments,
            "class_names": class_names,
            "attributes": attributes,
            "method_names": method_names,
            "variables": variables,
            "file_name": os.path.basename(src_file).split(".")[0].strip(),
            "package_name": package_name,
        }

    return src_files


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
        split_tokens = [token for token in split_tokens if token != ""]
        if len(split_tokens) > 1:
            returning_tokens.remove(token)
            for st in split_tokens:
                camel_split = inflection.underscore(st).split("_")
                camel_split = [token for token in camel_split if token != ""]
                if len(camel_split) > 1:
                    returning_tokens.append(st)
                    returning_tokens += camel_split
                # hyphen_split = inflection.hyphen(st).split("-")
                # if len(hyphen_split) > 1:
                #     returning_tokens.append(st)
                #     returning_tokens += hyphen_split
                else:
                    returning_tokens.append(st)
        else:
            camel_split = inflection.underscore(token).split("_")
            camel_split = [token for token in camel_split if token != ""]
            if len(camel_split) > 1:
                returning_tokens += camel_split
            # hyphen_split = inflection.underscore(token).split("_")
            # if len(hyphen_split) > 1:
            #     returning_tokens += hyphen_split

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


def preprocess_all_contents(src_files):
    for src in src_files.values():
        src["all_content"] = tokenize(src["all_content"])
        src["all_content"] = split_camelcase(src["all_content"])
        src["all_content"] = normalize(src["all_content"])
        src["all_content"] = remove_stopwords(src["all_content"])
        src["all_content"] = remove_java_keywords(src["all_content"])
        src["all_content"] = stem(src["all_content"])


def preprocess_pos_comments(src_files):
    for src in src_files.values():
        src["pos_tagged_comments"] = pos_tagging(src["comments"])
        src["pos_tagged_comments"] = split_camelcase(src["pos_tagged_comments"])
        src["pos_tagged_comments"] = normalize(src["pos_tagged_comments"])
        src["pos_tagged_comments"] = remove_java_keywords(src["pos_tagged_comments"])
        src["pos_tagged_comments"] = stem(src["pos_tagged_comments"])


def preprocess_comments(src_files):
    for src in src_files.values():
        src["comments"] = tokenize(src["comments"])
        src["comments"] = split_camelcase(src["comments"])
        src["comments"] = normalize(src["comments"])
        src["comments"] = remove_stopwords(src["comments"])
        src["comments"] = remove_java_keywords(src["comments"])
        src["comments"] = stem(src["comments"])


def preprocess_class_names(src_files):
    for src in src_files.values():
        src["class_names"] = split_camelcase(src["class_names"])
        src["class_names"] = normalize(src["class_names"])
        src["class_names"] = remove_stopwords(src["class_names"])
        src["class_names"] = remove_java_keywords(src["class_names"])
        src["class_names"] = stem(src["class_names"])


def preprocess_attributes(src_files):
    for src in src_files.values():
        src["attributes"] = split_camelcase(src["attributes"])
        src["attributes"] = normalize(src["attributes"])
        src["attributes"] = remove_stopwords(src["attributes"])
        src["attributes"] = remove_java_keywords(src["attributes"])
        src["attributes"] = stem(src["attributes"])


def preprocess_method_names(src_files):
    for src in src_files.values():
        src["method_names"] = split_camelcase(src["method_names"])
        src["method_names"] = normalize(src["method_names"])
        src["method_names"] = remove_stopwords(src["method_names"])
        src["method_names"] = remove_java_keywords(src["method_names"])
        src["method_names"] = stem(src["method_names"])


def preprocess_variables(src_files):
    for src in src_files.values():
        src["variables"] = split_camelcase(src["variables"])
        src["variables"] = normalize(src["variables"])
        src["variables"] = remove_stopwords(src["variables"])
        src["variables"] = remove_java_keywords(src["variables"])
        src["variables"] = stem(src["variables"])


def preprocess_file_name(src_files):
    for src in src_files.values():
        src["exact_file_name"] = src["file_name"]
        src["file_name"] = split_camelcase(src["file_name"])
        src["file_name"] = normalize(src["file_name"])
        src["file_name"] = remove_stopwords(src["file_name"])
        src["file_name"] = remove_java_keywords(src["file_name"])
        src["file_name"] = stem(src["file_name"])


def process_src():
    src_files = src_parser(
        "/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/IR_localisation/project/src/main/"
    )

    # print(src_files.keys())
    preprocess_pos_comments(src_files=src_files)
    preprocess_comments(src_files=src_files)
    preprocess_all_contents(src_files=src_files)
    preprocess_class_names(src_files=src_files)
    preprocess_method_names(src_files=src_files)
    preprocess_attributes(src_files=src_files)
    preprocess_file_name(src_files=src_files)

    preprocess_variables(src_files=src_files)

    out_file = open("source.json", "w")

    json.dump(src_files, out_file, indent=6)

    out_file.close()
