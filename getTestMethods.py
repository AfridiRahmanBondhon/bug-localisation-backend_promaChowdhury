import os
import javalang
import subprocess
import re
import concurrent.futures
import xml.etree.ElementTree as ET
import shutil
import json


def find_test_methods(java_code):
    test_methods = []

    tree = javalang.parse.parse(java_code)

    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration) and "Test" in node.name:
            for method in node.methods:
                if any(
                    annotation.name == "Test" for annotation in method.annotations
                ) or method.name.startswith("test"):
                    test_methods.append(method.name)

    return test_methods


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
                        test_classes_and_methods[file] = test_methods

    return test_classes_and_methods


def get_all_test_methods():
    folder_path = "/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/src/test/"
    test_classes_and_methods = find_test_classes_and_methods(folder_path)
    test_all_methods = []
    for java_file, test_methods in test_classes_and_methods.items():
        # print(f"Java file: {java_file[0:len(java_file)-5]}")
        methods = []
        for method in test_methods:
            test_all_methods.append(
                {"class": java_file[0 : len(java_file) - 5], "method": method}
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
        f"/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/{test_class}-{test_method}.xml",
    )


def getCoverage(test):
    run_jacoco(test_class=test["class"], test_method=test["method"])
    xml_file_path = "/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/target/site/jacoco/jacoco.xml"

    with open(xml_file_path, "r") as file:
        xml_data = file.read()

    root = ET.fromstring(xml_data)
    coverage_dict = {}

    for counter_elem in root.findall(".//counter"):
        counter_type = counter_elem.get("type")
        missed = int(counter_elem.get("missed"))
        covered = int(counter_elem.get("covered"))

        coverage_dict[counter_type] = {
            "missed": missed,
            "covered": covered,
        }

    return {"class": test["class"], "method": test["method"], "coverage": coverage_dict}


def process_test(test):
    print(test)
    return getCoverage(test)


def getTestStats():
    tests = get_all_test_methods()
    test_stats = []

    for test in tests:
        print(test)
        test_stats.append(getCoverage(test))

    # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    #     test_stats = list(executor.map(process_test, tests[:5]))
    return test_stats
    # with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    #     futures = [executor.submit(getCoverage, test) for test in tests[:5]]

    #     for future in concurrent.futures.as_completed(futures):
    #         try:
    #             result = future.result()
    #             print(result)
    #             test_stats.extend(result)
    #         except Exception as e:
    #             test_stats.extend({"Error": str(e)})
    with open("test_res.json", "w") as json_file:
        json.dump(test_stats, json_file)
    return test_stats
