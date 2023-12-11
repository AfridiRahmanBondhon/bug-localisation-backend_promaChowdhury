from fastapi import FastAPI
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from evaluation import evaluate
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from urllib.parse import urlparse
import re
import subprocess
import os
import json


class Github(BaseModel):
    link: str


def get_repo_info(url):
    pattern = r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<issue_number>\d+)"

    match = re.match(pattern, url)

    if match:
        repo_owner = match.group("owner")
        repo_name = match.group("repo")
        issue_number = match.group("issue_number")

        return repo_owner, repo_name, issue_number
    else:
        print("Invalid GitHub URL")


def delete_files():
    try:
        p = subprocess.Popen(
            [f"rm -rf report.json"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, stderr = p.communicate()
        output = output.decode("utf-8")

        p = subprocess.Popen(
            [f"rm -rf source.json"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, stderr = p.communicate()
        output = output.decode("utf-8")

        p = subprocess.Popen(
            [f"rm -rf project"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        p = subprocess.Popen(
            [f"rm -rf stack_trace.json"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        p = subprocess.Popen(
            [f"rm -rf token_matching.json"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        p = subprocess.Popen(
            [f"rm -rf semantic_similarity.json"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p = subprocess.Popen(
            [f"rm -rf vsm_similarity.json"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except:
        print("erorr")


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


app = FastAPI()
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/get_existing_evaluation_results/")
def get_results():
    json_file_path = "evaluation.json"
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            json_content = json.load(json_file)
        return json_content
    else:
        return {}


@app.post("/get_IR_report/")
async def get_report(github: Github):
    delete_files()
    repo_owner, repo_name, issue_number = get_repo_info(github.link)
    # return repo_owner, repo_name
    get_git_repo(f"https://github.com/{repo_owner}/{repo_name}.git")
    return evaluate(
        repo_name=repo_name, repo_owner=repo_owner, issue_number=int(issue_number)
    )
