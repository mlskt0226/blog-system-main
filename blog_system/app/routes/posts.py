from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
from app.database import db
from app.schemas import PostCreate, PostResponse
from app.models import Post

router = APIRouter(prefix="/posts", tags=["posts"])
templates = Jinja2Templates(directory="templates")

@router.post("/", response_model=PostResponse)
async def create_post(post: PostCreate):
    if post.authorId not in db.users:
        raise HTTPException(status_code=404, detail="Author not found")
    
    if not post.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    if not post.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    new_post = Post(
        id=db.next_post_id,
        authorId=post.authorId,
        title=post.title,
        content=post.content
    )
    
    db.posts[new_post.id] = new_post
    db.next_post_id += 1
    db.save_data()
    
    return new_post

@router.get("/", response_model=list[PostResponse])
async def get_posts():
    return list(db.posts.values())

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int):
    if post_id not in db.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return db.posts[post_id]

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, post: PostCreate):
    if post_id not in db.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.authorId not in db.users:
        raise HTTPException(status_code=404, detail="Author not found")
    
    if not post.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    if not post.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    db.posts[post_id].authorId = post.authorId
    db.posts[post_id].title = post.title
    db.posts[post_id].content = post.content
    db.posts[post_id].updatedAt = datetime.now()
    db.save_data()
    
    return db.posts[post_id]

@router.delete("/{post_id}")
async def delete_post(post_id: int):
    if post_id not in db.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    del db.posts[post_id]
    db.save_data()
    
    return {"message": "Post deleted successfully"}

# HTML endpoints
@router.get("/html/", response_class=HTMLResponse)
async def get_posts_html(request: Request):
    posts = list(db.posts.values())
    # Добавляем информацию об авторе к каждому посту
    posts_with_authors = []
    for post in posts:
        author = db.users.get(post.authorId)
        author_name = author.login if author else "Unknown"
        posts_with_authors.append({
            "post": post,
            "author_name": author_name
        })
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "posts": posts_with_authors}
    )

@router.get("/html/{post_id}", response_class=HTMLResponse)
async def get_post_html(request: Request, post_id: int):
    if post_id not in db.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = db.posts[post_id]
    author = db.users.get(post.authorId)
    author_name = author.login if author else "Unknown"
    
    return templates.TemplateResponse(
        "post.html",
        {"request": request, "post": post, "author_name": author_name}
    )

@router.get("/html/create/new", response_class=HTMLResponse)
async def create_post_form(request: Request):
    return templates.TemplateResponse(
        "create_post.html",
        {"request": request, "users": list(db.users.values())}
    )

@router.get("/html/edit/{post_id}", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int):
    if post_id not in db.posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = db.posts[post_id]
    return templates.TemplateResponse(
        "edit_post.html",
        {"request": request, "post": post, "users": list(db.users.values())}
    )