from fastapi import FastAPI
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from evaluation import evaluate
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from urllib.parse import urlparse


class Github(BaseModel):
    link: str
    issue_number: int


def get_repo_info(github_url):
    parsed_url = urlparse(github_url)

    path_components = parsed_url.path.strip("/").split("/")

    if len(path_components) == 2:
        repo_owner, repo_name = path_components
        return repo_owner, repo_name.replace(".git", "")
    else:
        print("Invalid GitHub repository URL.")
        return None, None


app = FastAPI()
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/get_IR_report/")
async def get_report(github: Github):
    repo_owner, repo_name = get_repo_info(github.link)
    return evaluate(
        repo_name=repo_name, repo_owner=repo_owner, issue_number=github.issue_number
    )
