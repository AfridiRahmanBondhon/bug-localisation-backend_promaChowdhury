from fastapi import FastAPI
from githubModel import Github
from fastapi.middleware.cors import CORSMiddleware
from getGitHubStats import count_languages, aggregate_complexity

# from getTestMethods import get_all_test_methods

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
    print(count_languages(link.link))

    return count_languages(link.link)


@app.post("/get_complexity")
async def get_aggregate_complexity():
    return aggregate_complexity()


# @app.post("/get_test_methods")
# async def get_test_methods():
#     return get_all_test_methods()
