import json
import pickle
from collections import OrderedDict


def get_traces_score(src_files, bug_reports):
    all_file_names = set(s["exact_file_name"] for s in src_files.values())

    all_scores = []
    report = bug_reports
    scores = []
    stack_traces = report["stack_trace"]

    # Preprocessing stack-traces
    final_st = []
    for trace in stack_traces:
        if trace[1] == "Unknown Source":
            final_st.append((trace[0].split(".")[-2].split("$")[0], trace[0].strip()))
        elif trace[1] != "Native Method":
            final_st.append((trace[1].split(".")[0].replace(" ", ""), trace[0].strip()))

    stack_traces = OrderedDict(
        [(file, package) for file, package in final_st if file in all_file_names]
    )

    for src in src_files.values():
        file_name = src["exact_file_name"]
        # If the source file has a package name
        if src["package_name"]:
            if (
                file_name in stack_traces
                and src["package_name"] in stack_traces[file_name]
            ):
                scores.append(1 / (list(stack_traces).index(file_name) + 1))

            else:
                # If it isn't the exact source file based on it's package name
                scores.append(0)
        # If it doesn't have a package name
        elif file_name in stack_traces:
            scores.append(1 / (list(stack_traces).index(file_name) + 1))
        else:
            scores.append(0)

    all_scores.append(scores)

    return all_scores


def stack_trace():
    with open("report.json", "r") as json_file:
        bug_reports = json.load(json_file)
    with open("source.json", "r") as json_file:
        src_files = json.load(json_file)

    trace_score = get_traces_score(src_files, bug_reports)
    out_file = open("stack_trace.json", "w")

    json.dump(trace_score[0], out_file, indent=6)

    out_file.close()
