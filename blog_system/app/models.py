from datetime import datetime
from typing import Dict, List

class User:
    def __init__(self, id: int, email: str, login: str, password: str):
        self.id = id
        self.email = email
        self.login = login
        self.password = password
        self.createdAt = datetime.now()
        self.updatedAt = datetime.now()

class Post:
    def __init__(self, id: int, authorId: int, title: str, content: str):
        self.id = id
        self.authorId = authorId
        self.title = title
        self.content = content
        self.createdAt = datetime.now()
        self.updatedAt = datetime.now()