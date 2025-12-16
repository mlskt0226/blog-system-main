import json
from typing import Dict, List
from app.models import User, Post
from datetime import datetime

class Database:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.posts: Dict[int, Post] = {}
        self.next_user_id = 1
        self.next_post_id = 1
        self.data_file = "data.json"
        self.load_data()
    
    def save_data(self):
        """Сохраняет данные в JSON файл"""
        data = {
            'users': [
                {
                    'id': user.id,
                    'email': user.email,
                    'login': user.login,
                    'password': user.password,
                    'createdAt': user.createdAt.isoformat(),
                    'updatedAt': user.updatedAt.isoformat()
                }
                for user in self.users.values()
            ],
            'posts': [
                {
                    'id': post.id,
                    'authorId': post.authorId,
                    'title': post.title,
                    'content': post.content,
                    'createdAt': post.createdAt.isoformat(),
                    'updatedAt': post.updatedAt.isoformat()
                }
                for post in self.posts.values()
            ],
            'next_user_id': self.next_user_id,
            'next_post_id': self.next_post_id
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        """Загружает данные из JSON файла"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Загружаем пользователей
            for user_data in data.get('users', []):
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    login=user_data['login'],
                    password=user_data['password']
                )
                user.createdAt = datetime.fromisoformat(user_data['createdAt'])
                user.updatedAt = datetime.fromisoformat(user_data['updatedAt'])
                self.users[user.id] = user
            
            # Загружаем посты
            for post_data in data.get('posts', []):
                post = Post(
                    id=post_data['id'],
                    authorId=post_data['authorId'],
                    title=post_data['title'],
                    content=post_data['content']
                )
                post.createdAt = datetime.fromisoformat(post_data['createdAt'])
                post.updatedAt = datetime.fromisoformat(post_data['updatedAt'])
                self.posts[post.id] = post
            
            self.next_user_id = data.get('next_user_id', 1)
            self.next_post_id = data.get('next_post_id', 1)
            
        except FileNotFoundError:
            # Файл не существует, начинаем с пустой базы
            pass

# Глобальный экземпляр базы данных
db = Database()