from fastapi import APIRouter, HTTPException
from app.database import db
from app.schemas import UserCreate, UserResponse
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Проверяем, существует ли пользователь с таким email или логином
    for existing_user in db.users.values():
        if existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing_user.login == user.login:
            raise HTTPException(status_code=400, detail="Login already taken")
    
    new_user = User(
        id=db.next_user_id,
        email=user.email,
        login=user.login,
        password=user.password
    )
    
    db.users[new_user.id] = new_user
    db.next_user_id += 1
    db.save_data()
    
    return new_user

@router.get("/", response_model=list[UserResponse])
async def get_users():
    return list(db.users.values())

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    if user_id not in db.users:
        raise HTTPException(status_code=404, detail="User not found")
    return db.users[user_id]

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserCreate):
    if user_id not in db.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем уникальность email и логина
    for existing_user in db.users.values():
        if existing_user.id != user_id:
            if existing_user.email == user.email:
                raise HTTPException(status_code=400, detail="Email already registered")
            if existing_user.login == user.login:
                raise HTTPException(status_code=400, detail="Login already taken")
    
    db.users[user_id].email = user.email
    db.users[user_id].login = user.login
    db.users[user_id].password = user.password
    db.users[user_id].updatedAt = datetime.now()
    db.save_data()
    
    return db.users[user_id]

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    if user_id not in db.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Удаляем также все посты пользователя
    posts_to_delete = [post_id for post_id, post in db.posts.items() if post.authorId == user_id]
    for post_id in posts_to_delete:
        del db.posts[post_id]
    
    del db.users[user_id]
    db.save_data()
    
    return {"message": "User deleted successfully"}