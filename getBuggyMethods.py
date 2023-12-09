import os
import javalang
import subprocess
import re
import concurrent.futures
import xml.etree.ElementTree as ET
import shutil
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import math
import joblib
import numpy


def find_similarity(doc1, doc2):
    vectorizer = TfidfVectorizer()
    documents = [doc1, doc2]
    tfidf_matrix = vectorizer.fit_transform(documents)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return cosine_sim[0, 1]


def find_test_methods(java_code):
    test_methods = []

    tree = javalang.parse.parse(java_code)

    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration) and "Test" in node.name:
            for method in node.methods:
                if any(annotation.name == "Test" for annotation in method.annotations):
                    test_methods.append(method.name)

    return test_methods


def path_to_classname(file_path):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    class_name = file_path.replace(os.path.sep, ".")
    class_name = class_name.replace(
        ".Users.promachowdhury.Desktop.fast-projects.bug-localisation-backend.project.src.test.java.",
        "",
    )
    class_name = class_name.replace(".java", "")

    return class_name


def find_test_classes_and_methods(folder_path):
    test_classes_and_methods = {}

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as java_file:
                    java_code = java_file.read()
                    test_methods = find_test_methods(java_code)
                    if test_methods:
                        test_classes_and_methods[
                            path_to_classname(file_path)
                        ] = test_methods

    return test_classes_and_methods


def extract_details_from_cdata(cdata_content, test_class_name, test_method_name):
    pattern = re.compile(rf"{test_class_name}\.{test_method_name}\(([^)]+)\)")

    match = pattern.search(cdata_content)
    if match:
        line_number = match.group(1)
        return line_number

    return None


def find_line_number(file_path, target_line):
    try:
        with open(file_path, "r") as file:
            for line_number, line in enumerate(file, start=1):
                if line_number == int(target_line):
                    return line.strip()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return None


def extract_line_number_from_cdata(line):
    match = re.search(r"\d+", line)

    if match:
        line_number = match.group()
        return line_number
    else:
        return None


def parse_test_cdata_from_file(file_path, class_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    test_cases = root.findall(".//testcase")
    for test_case in test_cases:
        test_name = test_case.get("name")
        class_name = test_case.get("classname")
        time_taken = test_case.get("time", "N/A")

        failure_element = test_case.find("failure")
        if failure_element is not None:
            failure_type = failure_element.get("type")
            cdata_content = failure_element.text.strip()

            line_number_cdata = extract_details_from_cdata(
                cdata_content, class_name, test_name
            )
            if line_number_cdata is not None:
                line_number = extract_line_number_from_cdata(line_number_cdata)

                return find_line_number(class_path, line_number)
        return None


def get_all_test_methods():
    folder_path = "/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/src/test/"
    test_classes_and_methods = find_test_classes_and_methods(folder_path)
    print(test_classes_and_methods.keys())
    test_all_methods = []
    for java_file, test_methods in test_classes_and_methods.items():
        # print(f"Java file: {java_file[0:len(java_file)-5]}")
        methods = []
        for method in test_methods:
            test_all_methods.append(
                {
                    "class": java_file,
                    "method": method,
                }
            )

    return test_all_methods


def run_jacoco(test_class, test_method):
    p = subprocess.Popen(
        [
            f"mvn clean verify -f /Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/pom.xml -Dtest={test_class}#{test_method} -Dmaven.test.failure.ignore=true -Drat.numUnapprovedLicenses=100"
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, stderr = p.communicate()
    output = output.decode("utf-8")
    shutil.copy(
        "/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/target/site/jacoco/jacoco.xml",
        f"/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/target/site/jacoco/{test_class}-{test_method}.xml",
    )


def parse_test_results_from_file(file_path):
    with open(file_path, "r") as file:
        file_content = file.read()

    runs_pattern = re.compile(r"Tests run: (\d+)")
    failures_pattern = re.compile(r"Failures: (\d+)")

    runs_match = runs_pattern.search(file_content)
    failures_match = failures_pattern.search(file_content)

    runs = int(runs_match.group(1)) if runs_match else None
    failures = int(failures_match.group(1)) if failures_match else None

    return runs, failures


def getScore(ef, ep, np, nf):
    model = joblib.load("random_forest_model.joblib")
    ef_perc = ef / (ef + ep + np + nf)
    ep_perc = ep / (ef + ep + np + nf)
    np_perc = np / (ef + ep + np + nf)
    nf_perc = nf / (ef + ep + np + nf)
    new_data = numpy.array([[ef_perc, ep_perc, np_perc, nf_perc]])

    probability = model.predict_proba(new_data)[:, 1]
    return probability[0]


def getBuggy():
    tests = get_all_test_methods()
    bug_stats = []
    method_coverage_dict = {}
    tests_to_run = tests

    tests_to_run = [
        {
            "class": "org.jsoup.nodes.AttributeTest",
            "method": "booleanAttributesAreNotCaseSensitive",
        }
    ]
    for test in tests_to_run:
        run_jacoco(test_class=test["class"], test_method=test["method"])

        file_path = f'/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/target/surefire-reports/{test["class"]}.txt'
        file_path_cdata = f'/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/target/surefire-reports/TEST-{test["class"]}.xml'
        class_name = test["class"].replace(".", "/")
        class_path = f"/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/src/test/java/{class_name}.java"
        runs, failures = parse_test_results_from_file(file_path)

        method_coverage_dict = parse_xml(
            xml_file=f'/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/target/site/jacoco/{test["class"]}-{test["method"]}.xml',
            method_coverage_dict=method_coverage_dict,
            runs=runs,
            failures=failures,
            class_path=class_path,
            file_path_cdata=file_path_cdata,
        )
    methods_suspicious = {}
    for methods in method_coverage_dict.keys():
        susp = getScore(
            method_coverage_dict[methods]["ef"],
            method_coverage_dict[methods]["ep"],
            method_coverage_dict[methods]["np"],
            method_coverage_dict[methods]["nf"],
        )
        methods_suspicious[methods] = {
            "class": method_coverage_dict[methods]["class"],
            "method": method_coverage_dict[methods]["method"],
            "desc": method_coverage_dict[methods]["desc"],
            "susp": susp * (method_coverage_dict[methods]["weight"] + 1)
            # "susp": (
            #     method_coverage_dict[methods]["ep"]
            #     / (
            #         method_coverage_dict[methods]["ep"]
            #         + method_coverage_dict[methods]["np"]
            #         + 1
            #     )
            #     / (
            #         (
            #             method_coverage_dict[methods]["ep"]
            #             / (
            #                 method_coverage_dict[methods]["ep"]
            #                 + method_coverage_dict[methods]["np"]
            #                 + 1
            #             )
            #         )
            #         + (
            #             method_coverage_dict[methods]["ef"]
            #             / (
            #                 method_coverage_dict[methods]["ef"]
            #                 + method_coverage_dict[methods]["nf"]
            #                 + 1
            #             )
            #         )
            #         + 1
            #     )
            # )
            # - method_coverage_dict[methods]["weight"],
        }

    sorted_dict = dict(
        sorted(
            methods_suspicious.items(), key=lambda item: item[1]["susp"], reverse=True
        )
    )
    return sorted_dict


def parse_xml(
    xml_file, method_coverage_dict, runs, failures, file_path_cdata, class_path
):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for class_element in root.findall(".//class"):
        class_name = class_element.get("name")

        for method_element in class_element.findall(".//method"):
            method_name = method_element.get("name")
            desc = method_element.get("desc")
            full_method_name = f"{class_name}/{method_name}/{desc}"
            covered = int(
                method_element.find('.//counter[@type="METHOD"]').get("covered")
            )
            # if full_method_name == "org/jsoup/nodes/LeafNode/attr":
            #     print(covered)
            if full_method_name not in method_coverage_dict:
                method_coverage_dict.setdefault(
                    full_method_name, {"ep": 0, "ef": 0, "np": 0, "nf": 0, "weight": 0}
                )

            line = parse_test_cdata_from_file(file_path_cdata, class_path)
            if line is not None:
                similarity = find_similarity(line, method_name)
            else:
                similarity = 0

            method_coverage_dict[full_method_name]["weight"] += similarity
            method_coverage_dict[full_method_name]["class"] = class_name
            method_coverage_dict[full_method_name]["method"] = method_name
            method_coverage_dict[full_method_name]["desc"] = desc

            if runs == 1 and failures == 1:
                if covered == 1:
                    method_coverage_dict[full_method_name]["ef"] += 1
                elif covered == 0:
                    method_coverage_dict[full_method_name]["nf"] += 1
            elif runs == 1 and failures == 0:
                if covered == 1:
                    method_coverage_dict[full_method_name]["ep"] += 1
                elif covered == 0:
                    method_coverage_dict[full_method_name]["np"] += 1

    return method_coverage_dict
