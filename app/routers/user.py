from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils
from ..database import engine, get_db
from typing import Optional, List, Union
from pydantic import BaseModel, HttpUrl
import requests



router = APIRouter(
    tags=["Users"]
)


#creating a new user
@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user:schemas.UserCreate, db: Session = Depends(get_db)):
    #first hash the password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    #add user to database
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    #lets try connecting to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': 'aferdoc', 'password': '1234567', 'sender': 'sambax', 'message': 'Hello,third message',
            'reciever': '256705579354'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)

    return new_user


#get one user
@router.get("/users/{id}", response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id{id} was not found")

    return user