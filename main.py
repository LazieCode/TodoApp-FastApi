from fastapi import FastAPI
import models
from database import engine
from routers import auth,todos

app = FastAPI()

models.Base.metadata.create_all(bind = engine)

app.include_router(auth.router) # With the help of this we will be able to run both main and auth with a single command of uvicorn and tags=["auth"] segreates the request calls of routes to one a different compartment in the same swagger.

app.include_router(todos.router) 
