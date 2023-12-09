from pydantic import BaseModel


class Github(BaseModel):
    link: str


class File(BaseModel):
    file_name: str
