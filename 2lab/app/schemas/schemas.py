from typing import Union
from pydantic import BaseModel


class User(BaseModel):
    email: str
    password: str

class Corpus(BaseModel):
    corpus_name: str
    text: str

class AlgorithmCall(BaseModel):
    word: str
    algorithm: str
    corpus_id: int