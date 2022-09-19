from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, admin_oauth2, user_oauth2, oauth2
from ..database import engine, get_db
from typing import Optional, List, Union
from pydantic import BaseModel, HttpUrl
import requests
import random
from random import randrange
from ..config import settings
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user_signup")



router = APIRouter(
    tags=["Users"]
)


#sign a new user
@router.post("/user_signup", status_code=status.HTTP_201_CREATED, response_model=schemas.Token)
def signup_user(user:schemas.UserCreate, db: Session = Depends(get_db)):
    #first create a random otp
    random_otp = random.randrange(1000, 10000)

    #create token
    access_token = user_oauth2.create_access_token(data={"otp": random_otp, "first_name": user.first_name,
                                                         "last_name": user.last_name, "phone_number": user.phone_number,
                                                         "password": user.password})
    #add logic for collecting payment from a user
    appendage = '256'
    number_string = str(user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    #send OTP to user
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'your Sambax OTP is {random_otp}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")


    return {"access_token": access_token, "token_type": "bearer"}




#creating a new user
@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.Token)
def create_user(given_otp:schemas.TokenOtp, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    token_data = user_oauth2.verify_access_token(token)

    if token_data.otp != given_otp.otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"you have given the wrong otp")

    #first hash the password
    hashed_password = utils.hash(token_data.password)
    #token_data.password = hashed_password

    #use a new dictionary to create the user
    thisdict = {
        "phone_number": f"{token_data.phone_number}",
        "password": f"{hashed_password}",
        "first_name": f"{token_data.first_name}",
        "last_name": f"{token_data.last_name}"
    }

    #add user to database
    new_user = models.User(**thisdict)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    #new_user_id = new_user.id
    # create token
    login_access_token = oauth2.create_access_token(data={"user_id": new_user.id})
    # return token

    return {"access_token": login_access_token, "token_type": "bearer"}

    #return new_user


#get one user
@router.get("/admin/users/{id}", response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id{id} was not found")

    return user


