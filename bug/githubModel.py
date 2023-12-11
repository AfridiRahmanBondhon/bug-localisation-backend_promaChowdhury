from pydantic import BaseModel
from typing import List


class Github(BaseModel):
    link: str


class File(BaseModel):
    file_name: str


class Limit(BaseModel):
    limit: int


class PayloadItem(BaseModel):
    class_name: str
    method_name: str


class TestCases(BaseModel):
    test_cases: List[PayloadItem]
