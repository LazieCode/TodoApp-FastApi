import sys
sys.path.append('..') #this will help us to properly able to import everything that is present in the parent directory of auth
from fastapi import APIRouter, status, Depends, HTTPException, Request,Response, Form
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # this library will be used to authenticate the user when they try to sign in. They will sign in via the OAuth2PasswordRequestForm
#JWT is a bearer token.. Bearer is a type of token and authorization platform.
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

SECRET_KEY = "lazy"
ALGO = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"])
models.Base.metadata.create_all(bind = engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl = "token")
templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "User unauthorized"}}
)


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        try:
            data = await self.request.form()
            self.username = data.get("email")
            self.password = data.get("password")
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid form")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user

def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta]= None):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow + timedelta(minutes=15)

    encode.update({"exp": expire}) 
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGO) 


async def get_current_user(request: Request,):
    try:
        token = request.cookies.get("token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username == None or user_id == None:
            logout(request)

        return {"username": username, "id": user_id}
    
    except:
        pass


@router.get("/users")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# @router.post("/create/user", status_code = status.HTTP_201_CREATED)
# async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
#     user_model = models.User()

#     user_model.username = create_user.username
#     user_model.email = create_user.email
#     user_model.first_name = create_user.first_name
#     user_model.last_name = create_user.last_name

#     hash_password = get_password_hash(create_user.password)
#     user_model.hashed_password = hash_password

#     user_model.is_active = True

#     db.add(user_model)
#     db.commit()

#     return user_model


@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        return False
    
    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username, user.id, expires_delta=token_expires)

    response.set_cookie(key="token", value=token, httponly=True)

    return True


@router.get("/", response_class = HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response, 
        form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Invalid username or password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        
        return response
    except HTTPException:
        msg = "Unknown Error" 
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

    
@router.get("/logout")
async def logout(request: Request):
    msg="Logout Successful"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="token")
    return response


@router.get("/register", response_class = HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class = HTMLResponse)
async def register_user(request: Request, email:str = Form(...), username:str = Form(...), firstname:str = Form(...), lastname:str = Form(...), password:str = Form(...), password2:str = Form(...), db: Session = Depends(get_db)):
    
    validation1 = db.query(models.User).filter(models.User.username == username).first()
    validation2 = db.query(models.User).filter(models.User.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration request"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

    user_model = models.User()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname
    hashed_password = get_password_hash(password)
    user_model.hashed_password = hashed_password
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg = "User successfully created"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

# Custom Exceptions

# def get_user_exception():
#     credentials_exception = HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, 
#                                         detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

#     return credentials_exception

# def token_exception():
#     token_exception_response = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                              detail="Incorrent username or password",
#                                              headers={"WWW-Authenticate": "Bearer"})

#     return token_exception_response




