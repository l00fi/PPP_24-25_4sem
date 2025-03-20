from typing import Union
from pydantic import BaseModel


class User(BaseModel):
    email: str
    password: str