import sys
sys.path.append('..') #this will help us to properly able to import everything that is present in the parent directory of auth

from fastapi import APIRouter, status, Depends, HTTPException
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


SECRET_KEY = "lazy"
ALGO = "HS256"


class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str


bcrypt_context = CryptContext(schemes=["bcrypt"])
models.Base.metadata.create_all(bind = engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl = "token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "User unauthorized"}}
)

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

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username == None or user_id == None:
            raise get_user_exception()

        return {"username": username, "id": user_id}
    
    except JWTError:
        raise get_user_exception()

@router.get("/users")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@router.post("/create/user", status_code = status.HTTP_201_CREATED)
async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
    user_model = models.User()

    user_model.username = create_user.username
    user_model.email = create_user.email
    user_model.first_name = create_user.first_name
    user_model.last_name = create_user.last_name

    hash_password = get_password_hash(create_user.password)
    user_model.hashed_password = hash_password

    user_model.is_active = True

    db.add(user_model)
    db.commit()

    return user_model


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise token_exception()
    
    token_expires = timedelta(minutes=20)
    token = create_access_token(user.username, user.id, expires_delta=token_expires)

    return {"token": token}



# Custom Exceptions

def get_user_exception():
    credentials_exception = HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, 
                                        detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    return credentials_exception

def token_exception():
    token_exception_response = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                             detail="Incorrent username or password",
                                             headers={"WWW-Authenticate": "Bearer"})

    return token_exception_response




