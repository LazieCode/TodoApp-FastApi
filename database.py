from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# First we need to connect to a sqlite database and that is done as follows.
#SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db" # a new file will be created named todos.db which will store all the our data 

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:pepsI123*@127.0.0.1:3306/todoapp"
#First step is to create the sqlalchemy engine.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

#Creating database session.
SessionLocal = sessionmaker(autocommit=False, autoflush= False, bind=engine)

Base = declarative_base() # This is basically the base class and we will import it in all our databases 