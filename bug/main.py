from fastapi import FastAPI
from fastapi import Request, Response
from githubModel import Github, File, Limit
from fastapi.middleware.cors import CORSMiddleware
from getGitHubStats import count_languages, aggregate_complexity
from fastapi.responses import FileResponse
import os
from getBuggyMethods import getBuggy, get_all_test_methods
from getTestMethods import getTestStats
from fastapi.responses import StreamingResponse
import time
import asyncio
import json
from pydantic import BaseModel
from typing import List


class PayloadItem(BaseModel):
    class_name: str
    method_name: str


class TestCases(BaseModel):
    test_cases: List[PayloadItem]


app = FastAPI()
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/get_statistics")
async def get_statistics(link: Github):
    return count_languages(link.link)


@app.post("/get_all_test_cases")
async def get_test_methods(res: Limit):
    if res.limit == 0:
        res.limit = 1
    json_file_path = "all_test_cases.json"
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            test_cases = json.load(json_file)
    else:
        test_cases = get_all_test_methods()

    if 10 * (res.limit - 1) > len(test_cases):
        return {"count": len(test_cases), "tests": test_cases[: len(test_cases)]}
    else:
        return {
            "count": len(test_cases),
            "tests": test_cases[(10 * (res.limit - 1)) : ((10 * (res.limit - 1)) + 10)],
        }


@app.post("/get_complexity")
async def get_aggregate_complexity():
    return aggregate_complexity()


@app.post("/get_test_methods")
async def get_test_methods(request: Request):
    tests = await request.json()
    # print(tests)
    return getTestStats(tests["test_cases"])


@app.post("/download-file")
def download_file(file: File):
    file_path = f"/Users/promachowdhury/Desktop/fast-projects/bug-localisation-backend/bug/project/{file.file_name}.xml"
    file_name = f"{file.file_name}.xml"

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(file_path, filename=file_name)


@app.post("/get_existing_buggy_methods")
def get_results():
    json_file_path = "bug_res.json"
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            json_content = json.load(json_file)
            print(json_content)
            return json_content
    else:
        return []


@app.post("/get_buggy_methods")
async def get_buggy_methods(request: Request):
    tests = await request.json()
    return getBuggy(tests["test_cases"])


test_cases = ["TestCase1", "TestCase2", "TestCase3"]
current_index = 0
sse_active = True


def get_next_test_result():
    for i in range(3):
        test_case = test_cases[current_index]
        current_index += 1

        return f"Result for {test_case}: PASS"
    else:
        return None


sse_active = True
test_cases = ["TestCase1", "TestCase2", "TestCase3"]


async def generate_test_results():
    for test_case in test_cases:
        test_result = f"Result for {test_case}: PASS"
        yield f"data: {test_result}\n\n"
        await asyncio.sleep(1)  # Adjust as needed


@app.get("/get_test_results")
async def sse_test_results(response: Response):
    response.headers["Content-Type"] = "text/event-stream"

    async def event_generator():
        async for data in generate_test_results():
            yield data

    return StreamingResponse(event_generator())


@app.get("/sse_test_results")
async def sse_test_results(response: Response):
    response.headers["Content-Type"] = "text/event-stream"

    async def event_generator():
        async for data in getTestStats():
            data_json = json.dumps(data)
            print(data_json)
            yield f"data: {data_json}\n\n".encode("utf-8")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
