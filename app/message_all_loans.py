#import datetime
#from fastapi import FastAPI, Response, status, HTTPException, Depends
#import config
from .config import settings
from . import models
#import database
#import models
#import schemas
#import utils
#from . import models, schemas, utils
#from sqlalchemy.orm import Session
from datetime import datetime, timedelta
#from database import engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests



x = datetime.now()
print(x)

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}/{settings.database_name}"
# an Engine, which the Session will use for connection
# resources
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# a sessionmaker(), also in the same scope as the engine
Session = sessionmaker(engine)

# we can now construct a Session() and include begin()/commit()/rollback()
# at once
with Session.begin() as session:
    #session.add(some_object)
    #session.add(some_other_object)
    loans = session.query(models.Loan).filter(models.Loan.running == True).all()
    if not loans:
        print("there are no results")
    for loan in loans:
        print("hello")
        #format_string = "%Y-%m-%d %H:%M:%S.%f"
        #expiry_date_string = str(loan.expiry_date)
        #expiry_date_object = datetime.strptime(expiry_date_string, format_string)
        #now_string = str(datetime.now())
        #now = datetime.strptime(now_string, format_string)
        #maturity_object = now-create_date
        #loan_maturity = maturity_object.days

        # get user
        user = session.query(models.User).filter(models.User.id == loan.user_id).first()
        # get user's phone number
        appendage = '256'
        number_string = str(user.phone_number)
        usable_phone_number_string = appendage + number_string
        usable_phone_number = int(usable_phone_number_string)

        # send reminder message to user
        # lets connect to box-uganda for messaging
        url = "https://boxuganda.com/api.php"
        data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}',
                'sender': 'sambax',
                'message': f'Hello {user.first_name}, Your loan balance with Sambax Finance Ltd is UgX{loan.loan_balance}.Your loan expires on {loan.expiry_date}.Please pay today to clear the loan.Thanks',
                'reciever': f'{usable_phone_number}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")







