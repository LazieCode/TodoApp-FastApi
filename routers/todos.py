
import sys
from fastapi import Request
sys.path.append('..') #this will help us to properly able to import everything that is present in the parent directory of auth
from fastapi import APIRouter, status, Depends,Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from .auth import get_current_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette import status

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Item not found"}}
)

models.Base.metadata.create_all(bind = engine)

templates = Jinja2Templates(directory="templates")

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request:Request, db:Session = Depends(get_db)):
    
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    

    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()
    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})


@router.get("/add-todo", response_class=HTMLResponse)
async def add_todo(request:Request):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})

@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...), description: str = Form(...), priority: int = Form(...), db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request:Request, todo_id:int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def update_todo(request: Request, todo_id:int, title: str = Form(...), description: str = Form(...), priority: int = Form(...), db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo.title = title
    todo.description = description
    todo.priority = priority

    db.add(todo)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)



@router.get("/delete/{todo_id}")
async def delete_todo(request:Request, todo_id:int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

    if todo is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.delete(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
    

@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request:Request, todo_id:int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

    if todo is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    todo.complete = not todo.complete

    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)



# class Todo(BaseModel):

#     title: str
#     description: Optional[str] =  Field(min_length=1, max_length=100)
#     priority: int = Field(gt=0, lt=6, description="Priority should be between 1 to 5")
#     complete: bool  


# @router.get("/test")
# async def test(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})


# @router.get("/")
# async def read_all(db: Session = Depends(get_db)): # Now the execution of this function depends on the execution of the get_db function so that is why we have used depends 
#     return db.query(models.Todos).all()

# @router.get("/user")
# async def read_all_by_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

#     # Dictionary is like this {username: ..., id: user_id}

#     if user is None:
#         raise get_user_exception()

#     return db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()


# @router.get("/{todo_id}")
# async def read_todo(todo_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    
#     if user is None:
#         raise get_user_exception()

#     todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

#     if todo_model is not None:
#         return todo_model

#     raise ItemNotFoundException()


# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_todo(todo: Todo, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

#     if user is None:
#         raise get_user_exception()

#     todo_model = models.Todos()
#     todo_model.title = todo.title
#     todo_model.description = todo.description
#     todo_model.priority = todo.priority
#     todo_model.complete = todo.complete
#     todo_model.owner_id = user.get("id")

#     db.add(todo_model)
#     db.commit()

#     return succesful_response(201)


# @router.put("/{todo_id}")
# async def update_todo(todo_id:int, todo: Todo, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

#     if user is None:
#         raise get_user_exception()

#     todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

#     if todo_model is None:
#         raise ItemNotFoundException()
    
#     todo_model.title = todo.title
#     todo_model.description = todo.description
#     todo_model.priority = todo.priority
#     todo_model.complete = todo.complete
#     todo_model.owner_id = user.get("id")

#     db.add(todo_model)
#     db.commit()

#     return succesful_response(200)


# @router.delete('/{todo_id}')
# async def delete_todo(todo_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

#     if user is None:
#         raise get_user_exception()

#     todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    
#     if todo_model is None:
#         raise ItemNotFoundException()

#     db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).delete()

#     db.commit()

#     return succesful_response(200)


# def succesful_response(status_code: int):
#     return{
#         'status': status_code,
#         'message': 'Successful'
#     }

# def ItemNotFoundException():
#     return HTTPException(status_code=404, detail="Item not found")