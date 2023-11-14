import os
import javalang
import subprocess
import re
import concurrent.futures
import xml.etree.ElementTree as ET


def find_test_methods(java_code):
    test_methods = []

    tree = javalang.parse.parse(java_code)

    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration) and "Test" in node.name:
            for method in node.methods:
                if any(annotation.name == "Test" for annotation in method.annotations):
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
            f"mvn clean verify -f /Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/pom.xml -Dtest={test_class}#{test_method}"
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, stderr = p.communicate()
    output = output.decode("utf-8")

    p = subprocess.Popen(
        [
            f"mvn clean verify -f /Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/pom.xml -Dtest={test_class}#{test_method}"
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, stderr = p.communicate()
    output = output.decode("utf-8")


def getTestStas():
    tests = get_all_test_methods()
    test_stats = {}
    for test in tests[:5]:
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

            print(coverage_dict)


getTestStas()
