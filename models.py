from turtle import back
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, index=True)
    username = Column(String(45), unique=True, index=True)
    first_name = Column(String(45))
    last_name = Column(String(45))
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)

    todos = relationship("Todos", back_populates="owner") # Creating a relationship between the two tables.

#Creating a todos table
class Todos(Base):
    __tablename__ = "TodoList"  # actual table name

    # Now defining the columns for the table. id, title, description, priority, status

    id = Column(Integer, primary_key = True, index = True)
    title = Column(String(200))
    description = Column(String(45))
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("Users.id"))

    owner = relationship("User", back_populates="todos")
