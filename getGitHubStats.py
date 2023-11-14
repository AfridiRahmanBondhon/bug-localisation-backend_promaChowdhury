import subprocess
import re
import os
import glob
import fnmatch
import javalang
import subprocess
import re
import concurrent.futures


def get_java_files(directory_path):
    java_files = []

    for root, dirnames, filenames in os.walk(directory_path):
        for filename in fnmatch.filter(filenames, "*.java"):
            java_files.append(os.path.join(root, filename))

    return java_files


def extract_method_names(file_path):
    with open(file_path, "r") as file:
        tree = javalang.parse.parse(file.read())

        method_names = []
        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                start_line = node.position.line
                method_names.append({"method_name": node.name, "line": start_line})

    return method_names


def get_complexity(file_name):
    p = subprocess.Popen(
        [
            f"java -jar /Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/lib/checkstyle-5.9-all.jar -c check.xml {file_name}"
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, stderr = p.communicate()
    output = output.decode("utf-8")

    pattern = r"(\S+\.java):(\d+):\d+: Cyclomatic Complexity is (\d+)"

    matches = re.finditer(pattern, output)

    file_info = []
    for match in matches:
        filename = match.group(1)
        line_number = match.group(2)
        complexity = match.group(3)
        file_info.append(
            {
                "File": filename,
                "Line Number": line_number,
                "Cyclomatic Complexity": complexity,
            }
        )

    return file_info


def aggregate_complexity():
    method_names = {}
    complexity = []

    java_files = get_java_files(
        "/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/project/src/"
    )

    for file in java_files:
        method_names[file] = extract_method_names(file)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(get_complexity, file_path) for file_path in java_files
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                complexity.extend(result)
            except Exception as e:
                complexity.extend({"Error": str(e)})

    for res in complexity:
        meth_list = method_names[res["File"]]
        methods = [m["method_name"] for m in meth_list]
        lines = [m["line"] for m in meth_list]

        method_line = next(
            (i for i, r in enumerate(lines) if int(res["Line Number"]) <= r),
            len(lines) - 1,
        )
        if method_line != -1:
            res["method_name"] = methods[method_line]
        else:
            res["method_name"] = "unamed"
    return complexity


def get_git_repo(link):
    repo_url = link

    local_directory = "project"
    try:
        subprocess.run(["mkdir", local_directory], check=True)
        print("Repository created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

    try:
        subprocess.run(["git", "clone", repo_url, local_directory], check=True)
        print("Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def count_languages(link):
    get_git_repo(link)
    directory_path = "project"
    try:
        # Run cloc and capture its output
        cloc_output = subprocess.check_output(
            ["cloc", directory_path], universal_newlines=True
        )

        # Extract code, comments, and blank lines counts using regular expressions
        language_lines = re.findall(
            r"^([A-Za-z]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", cloc_output, re.MULTILINE
        )

        # Create a dictionary to store language names as keys and their corresponding line numbers as values
        language_line_counts = {}
        for language, files, blank, comment, code in language_lines:
            language_line_counts[language] = {
                "files": int(files),
                "blank": int(blank),
                "comment": int(comment),
                "code": int(code),
            }

        return language_line_counts
    except subprocess.CalledProcessError:
        print("Error: Failed to run cloc.")
        return None


def count_lines_of_code(file_path):
    with open(file_path, "rb") as file:
        try:
            lines = file.read().decode("utf-8")
        except UnicodeDecodeError:
            lines = file.read().decode("ISO-8859-1")
        return len(lines.splitlines())


def count_lines_in_directory(directory_path):
    file_info = {}
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            code_lines = count_lines_of_code(file_path)
            file_info[file_name] = code_lines
    print(file_info)
    return file_info


# get_git_repo("https://github.com/jhy/jsoup.git")

# Specify the path to your Python project directory
project_directory = "project"
count_lines_in_directory("project")
