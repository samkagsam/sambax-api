from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, admin_oauth2, user_oauth2, oauth2, password_recover_oauth2
from ..database import engine, get_db
from typing import Optional, List, Union
from pydantic import BaseModel, HttpUrl
import requests
import random
from random import randrange
from ..config import settings
from fastapi.security import OAuth2PasswordBearer
from ..config import settings
from twilio.rest import Client


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user_signup")
oauth2_scheme2 = OAuth2PasswordBearer(tokenUrl="forgot_password")



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
                                                         "password": user.password, "customer_image_url": user.customer_image_url,
                                                         "customer_id_url": user.customer_id_url})
    #add logic for getting usable phone number of a user
    appendage = '+256'
    number_string = str(user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    # send OTP to user using twilio
    # Set environment variables for your credentials
    # Read more at http://twil.io/secure
    account_sid = settings.twilio_account_sid
    auth_token = settings.twilio_auth_token
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"Your verification code is {random_otp}",
        from_="SAMBAX",
        to=usable_phone_number
    )

    print(message.sid)

    return {"access_token": access_token, "token_type": "bearer"}




#creating a new user
@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=schemas.Token)
def create_user(given_otp:schemas.TokenOtp, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    token_data = user_oauth2.verify_access_token(token)

    if token_data.otp != given_otp.otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"you have given the wrong otp")

    #first hash the password
    hashed_password = utils.hash(token_data.password)

    #let us put together the urls of the customer
    #this format:https://sambaxfinance.com/media/images/Tenywa/TENYWA.jpg
    #customer_image_url_string = f"https://sambaxfinance.com/media/images/{token_data.phone_number}/{token_data.customer_image_url}"
    #customer_id_url_string = f"https://sambaxfinance.com/media/images/{token_data.phone_number}/{token_data.customer_id_url}"

    #let us get the network of the customer
    number_string = str(token_data.phone_number)
    num_list = list(number_string)
    num_list_index_zero = num_list[0]
    num_list_index_one = num_list[1]
    #num_list_index_two = num_list[2]
    newtwork_string = num_list_index_zero + num_list_index_one
    #print(newtwork_string)

    if newtwork_string == "70" or newtwork_string =="75" or newtwork_string =="74":
        network = "airtel"
    elif newtwork_string == "77" or newtwork_string =="78" or newtwork_string =="76":
        network = "mtn"
    else:
        network = "other"

    #print(network)



    #use a new dictionary to create the user
    thisdict = {
        "phone_number": f"{token_data.phone_number}",
        "password": f"{hashed_password}",
        "first_name": f"{token_data.first_name}",
        "last_name": f"{token_data.last_name}",
        "customer_image_url": f"https://sambaxfinance.com/media/images/{token_data.phone_number}/{token_data.customer_image_url}",
        "customer_id_url": f"https://sambaxfinance.com/media/images/{token_data.phone_number}/{token_data.customer_id_url}",
        "network": f"{network}"
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


#landing page for a user after logging in or signing up
@router.get("/landing_page", response_model=schemas.LandingPage)
def land_user( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    account_balance = str(current_user.account_balance)
    first_name = current_user.first_name
    loan_status = ""
    current_loan = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True).first()

    if not current_loan:
        loan_status = "you have no active loan with Sambax Finance"
        #raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you have no active loan")

    else:
        loan_balance = current_loan.loan_balance
        # convert loan balance to string
        loan_status = str(loan_balance)

    #expiry_date = current_loan.expiry_date

    return {"first_name": first_name, "account_balance": account_balance, "loan_balance": loan_status}


#for a user who has forgotten their password
@router.post("/forgot_password", status_code=status.HTTP_201_CREATED, response_model=schemas.Token)
def check_user_phone_number(user:schemas.PhoneNumberRecover, db: Session = Depends(get_db)):
    #first check if the phone number given is registered with sambax
    user_inquired = db.query(models.User).filter(models.User.phone_number == user.phone_number).first()
    if not user_inquired:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with phone number {user.phone_number} was not found")

    #first create a random otp
    random_otp = random.randrange(1000, 10000)

    #create token
    access_token = password_recover_oauth2.create_access_token(data={"otp": random_otp,
                                                          "phone_number": user.phone_number
                                                         })
    #add logic for getting usable phone number of a user
    appendage = '+256'
    number_string = str(user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    # send OTP to user
    # Set environment variables for your credentials
    # Read more at http://twil.io/secure
    account_sid = settings.twilio_account_sid
    auth_token = settings.twilio_auth_token
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"Your verification code is {random_otp}",
        from_="SAMBAX",
        to=usable_phone_number
    )

    print(message.sid)

    return {"access_token": access_token, "token_type": "bearer"}


#validating the otp for new password
@router.post("/otp_validate", status_code=status.HTTP_201_CREATED, response_model=schemas.Token)
def validate_user_otp_password_recover(given_otp:schemas.TokenOtp, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme2)):
    token_data = password_recover_oauth2.verify_access_token(token)

    if token_data.otp != given_otp.otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"you have given the wrong otp")

    # get the user_id of the user
    user = db.query(models.User).filter(models.User.phone_number == token_data.phone_number).first()

    # create token
    login_access_token = oauth2.create_access_token(data={"user_id": user.id})
    # return token

    return {"access_token": login_access_token, "token_type": "bearer"}


#update password of user
@router.post("/password_update", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def update_user_password(givenPassword: schemas.PasswordChange, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):


    #first hash the given password
    hashed_password = utils.hash(givenPassword.password)

    # use a random dictionary to update the password
    thisdict = {

        "password": "xyz"
    }

    thisdict["password"] = hashed_password

    #update the password of the user
    password_query = db.query(models.User).filter(models.User.id == current_user.id)
    password_query.update(thisdict, synchronize_session=False)
    db.commit()

    return current_user


#get one user
@router.post("/admin/get_user_id", response_model=schemas.UserOut)
def admin_get_user_id(given_number: schemas.PhoneNumberRecover, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    user = db.query(models.User).filter(models.User.phone_number == given_number.phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    return user




