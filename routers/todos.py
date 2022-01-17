import sys
sys.path.append('..') #this will help us to properly able to import everything that is present in the parent directory of auth

from fastapi import APIRouter, status, HTTPException, Depends # standds for dependencies
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from .auth import get_current_user, get_user_exception

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Item not found"}}
)

models.Base.metadata.create_all(bind = engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class Todo(BaseModel):

    title: str
    description: Optional[str] =  Field(min_length=1, max_length=100)
    priority: int = Field(gt=0, lt=6, description="Priority should be between 1 to 5")
    complete: bool  


@router.get("/")
async def read_all(db: Session = Depends(get_db)): # Now the execution of this function depends on the execution of the get_db function so that is why we have used depends 
    return db.query(models.Todos).all()

@router.get("/user")
async def read_all_by_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    # Dictionary is like this {username: ..., id: user_id}

    if user is None:
        raise get_user_exception()

    return db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()


@router.get("/{todo_id}")
async def read_todo(todo_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

    if todo_model is not None:
        return todo_model

    raise ItemNotFoundException()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: Todo, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()

    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return succesful_response(201)


@router.put("/{todo_id}")
async def update_todo(todo_id:int, todo: Todo, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

    if todo_model is None:
        raise ItemNotFoundException()
    
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return succesful_response(200)


@router.delete('/{todo_id}')
async def delete_todo(todo_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    
    if todo_model is None:
        raise ItemNotFoundException()

    db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).delete()

    db.commit()

    return succesful_response(200)


def succesful_response(status_code: int):
    return{
        'status': status_code,
        'message': 'Successful'
    }

def ItemNotFoundException():
    return HTTPException(status_code=404, detail="Item not found")