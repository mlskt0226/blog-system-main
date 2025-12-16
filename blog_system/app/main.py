from fastapi import FastAPI, Request, HTTPException, Query, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Blog Platform API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# ---------- МОДЕЛИ (для API/валидатора) ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class PostCreate(BaseModel):
    title: str
    content: str

class Post(BaseModel):
    id: int
    title: str
    content: str
    user_id: int

# ---------- ФЕЙКОВАЯ "БД" ----------
users_db = [
    {"id": 1, "username": "admin", "email": "admin@test.com", "role": "ADMIN", "password": "123"}
]
posts_db: List[dict] = []
comments_db: List[dict] = []
favorites_db = {}

# ✅ app.state ПЕРЕМЕЩЕН ПОСЛЕ app создания
app.state.favorites_db = favorites_db

# ---------- СЕССИИ ----------
def get_current_user_id(request: Request) -> int:
    user_id_str = request.cookies.get("user_id")
    if user_id_str:
        try:
            return int(user_id_str)
        except ValueError:
            pass
    return 1

# ---------- HTML ГЛАВНАЯ С ПОИСКОМ ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: Optional[str] = None):
    data = posts_db
    if q:
        q_lower = q.lower()
        data = [
            p for p in posts_db
            if q_lower in p["title"].lower() or q_lower in p["content"].lower()
        ]

    comments_by_post = {}
    for c in comments_db:
        comments_by_post.setdefault(c["post_id"], []).append(c)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": data,
            "comments_by_post": comments_by_post,
            "title": "Главная — Блог",
            "favorites_db": favorites_db,  # ✅ для шаблона
        }
    )

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: Optional[str] = None, page: int = 1):
    per_page = 5  # постов на странице
    data = posts_db
    
    if q:
        q_lower = q.lower()
        data = [p for p in posts_db if q_lower in p["title"].lower() or q_lower in p["content"].lower()]
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = data[start:end]
    
    total_pages = (len(data) + per_page - 1) // per_page
    
    comments_by_post = {}
    for c in comments_db:
        comments_by_post.setdefault(c["post_id"], []).append(c)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": paginated_posts,
            "comments_by_post": comments_by_post,
            "title": "Главная — Блог",
            "favorites_db": favorites_db,
            "page": page,
            "total_pages": total_pages,
            "q": q,
        }
    )


# ---------- HTML СТРАНИЦЫ РЕГИСТРАЦИИ/ЛОГИНА ----------
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "title": "Регистрация"}
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "title": "Вход"}
    )

# ---------- LOGOUT ----------
@app.get("/logout")
def logout(response: Response):
    response.delete_cookie("user_id")
    return RedirectResponse(url="/", status_code=303)

# ---------- РЕГИСТРАЦИЯ / ЛОГИН (ФОРМЫ) ----------
@app.post("/auth/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    if any(u["email"] == email for u in users_db):
        raise HTTPException(status_code=400, detail="Email уже используется")

    new_user = {
        "id": len(users_db) + 1,
        "username": username,
        "email": email,
        "role": "USER",
        "password": password,
    }
    users_db.append(new_user)
    return RedirectResponse(url="/login", status_code=303)

@app.post("/auth/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
):
    user_db = next((u for u in users_db if u["email"] == email), None)
    if not user_db or user_db["password"] != password:
        raise HTTPException(status_code=401, detail="Неверный логин/пароль")

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user_db["id"]), httponly=True)
    return response

# ---------- ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ----------
@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    current_user_id = get_current_user_id(request)
    user = next((u for u in users_db if u["id"] == current_user_id), None)

    class Obj:
        pass

    user_obj = None
    if user:
        user_obj = Obj()
        user_obj.id = user["id"]
        user_obj.username = user["username"]
        user_obj.email = user["email"]
        user_obj.role = user["role"]

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Профиль",
            "user": user_obj,
        }
    )

@app.post("/profile", response_class=HTMLResponse)
def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
):
    current_user_id = get_current_user_id(request)
    user = next((u for u in users_db if u["id"] == current_user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if any(u["email"] == email and u["id"] != current_user_id for u in users_db):
        raise HTTPException(status_code=400, detail="Email уже используется другим пользователем")

    user["username"] = username
    user["email"] = email

    class Obj:
        pass
    user_obj = Obj()
    user_obj.id = user["id"]
    user_obj.username = user["username"]
    user_obj.email = user["email"]
    user_obj.role = user["role"]

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Профиль",
            "user": user_obj,
        }
    )

# ---------- CRUD ПОСТОВ + ФИЛЬТРЫ ----------
@app.post("/posts/")
def create_post(title: str = Form(...), content: str = Form(...)):  # ✅ УБРАЛ async и Request
    new_post = {
        "id": len(posts_db) + 1,
        "title": title,
        "content": content,
        "user_id": 1
    }
    posts_db.append(new_post)
    return RedirectResponse(url="/", status_code=303)

@app.get("/posts/", response_model=List[Post])
def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = None,
):
    data = posts_db
    if user_id is not None:
        data = [p for p in posts_db if p["user_id"] == user_id]

    start = (page - 1) * limit
    end = start + limit
    return data[start:end]

@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return post

@app.put("/posts/{post_id}")
def update_post(post_id: int, post: PostCreate):
    for p in posts_db:
        if p["id"] == post_id:
            p["title"] = post.title
            p["content"] = post.content
            return {"message": "Пост обновлён", "post": p}
    raise HTTPException(status_code=404, detail="Пост не найден")

# ---------- РЕДАКТИРОВАНИЕ И УДАЛЕНИЕ ПОСТОВ ----------
@app.post("/posts/{post_id}/edit")
def edit_post(post_id: int, title: str = Form(...), content: str = Form(...)):
    for post in posts_db:
        if post["id"] == post_id:
            post["title"] = title
            post["content"] = content
            break
    return RedirectResponse(url="/", status_code=303)

@app.post("/posts/{post_id}/delete")
def delete_post(post_id: int):
    global posts_db, comments_db, favorites_db
    posts_db = [p for p in posts_db if p["id"] != post_id]
    comments_db = [c for c in comments_db if c["post_id"] != post_id]
    for user_id in list(favorites_db.keys()):
        favorites_db[user_id] = [pid for pid in favorites_db[user_id] if pid != post_id]
    return RedirectResponse(url="/", status_code=303)

    
    # Удаляем связанные комментарии
    global comments_db
    comments_db = [c for c in comments_db if c["post_id"] != post_id]
    
    # Удаляем из избранного у всех пользователей
    for user_favs in favorites_db.values():
        user_favs[:] = [pid for pid in user_favs if pid != post_id]
    
    return RedirectResponse(url="/", status_code=303)


# ---------- КОММЕНТАРИИ К ПОСТАМ ----------
@app.post("/posts/{post_id}/comments")
def create_comment(
    post_id: int,
    author: str = Form(...),
    text: str = Form(...),
):
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    new_comment = {
        "id": len(comments_db) + 1,
        "post_id": post_id,
        "author": author,
        "text": text,
    }
    comments_db.append(new_comment)
    return RedirectResponse(url="/", status_code=303)

@app.get("/posts/{post_id}/comments")
def get_comments(post_id: int):
    return [c for c in comments_db if c["post_id"] == post_id]

# ---------- ИЗБРАННЫЕ ПОСТЫ ----------
@app.post("/posts/{post_id}/favorite")
def add_favorite(post_id: int, request: Request):
    current_user_id = get_current_user_id(request)
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    favs = favorites_db.setdefault(current_user_id, [])
    if post_id not in favs:
        favs.append(post_id)

    return RedirectResponse(url="/favorites", status_code=303)

@app.post("/posts/{post_id}/unfavorite")
def remove_favorite(post_id: int, request: Request):
    current_user_id = get_current_user_id(request)
    post = next((p for p in posts_db if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    favs = favorites_db.get(current_user_id, [])
    if post_id in favs:
        favs.remove(post_id)
        if not favs:
            del favorites_db[current_user_id]

    return RedirectResponse(url="/favorites", status_code=303)

@app.get("/favorites", response_class=HTMLResponse)
def favorites_page(request: Request):
    current_user_id = get_current_user_id(request)
    fav_ids = favorites_db.get(current_user_id, [])
    fav_posts = [p for p in posts_db if p["id"] in fav_ids]

    comments_by_post = {}
    for c in comments_db:
        comments_by_post.setdefault(c["post_id"], []).append(c)

    return templates.TemplateResponse(
        "favorites.html",
        {
            "request": request,
            "title": "Избранные посты",
            "posts": fav_posts,
            "comments_by_post": comments_by_post,
            "favorites_db": favorites_db,  # ✅ для шаблона
        }
    )

# ---------- ПОИСК ПОСТОВ И ПОЛЬЗОВАТЕЛЕЙ (API) ----------
@app.get("/search/posts/")
def search_posts(q: str, page: int = 1, limit: int = 10):
    start = (page - 1) * limit
    results = [
        p for p in posts_db
        if q.lower() in p["title"].lower() or q.lower() in p["content"].lower()
    ]
    return results[start:start + limit]

@app.get("/search/users/")
def search_users(q: str):
    return [
        u for u in users_db
        if q.lower() in u["username"].lower() or q.lower() in u["email"].lower()
    ]
