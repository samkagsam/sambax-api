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
        format_string = "%Y-%m-%d %H:%M:%S.%f"
        expiry_date_string = str(loan.expiry_date)
        expiry_date_object = datetime.strptime(expiry_date_string, format_string)
        now_string = str(datetime.now())
        now = datetime.strptime(now_string, format_string)
        #maturity_object = now-create_date
        #loan_maturity = maturity_object.days

        if now > expiry_date_object :
            #print("hehe")
            #get the loan balance and compound it
            interest = 0.01*loan.loan_balance
            new_loan_balance = loan.loan_balance + interest

            # update the loan balance
            thisdict = {

                "loan_balance": 1964
            }

            thisdict["loan_balance"] = new_loan_balance

            # update the loan balance of the user
            loan_query = session.query(models.Loan).filter(models.Loan.user_id == loan.user_id,
                                                      models.Loan.running == True)
            loan_query.update(thisdict, synchronize_session=False)
            session.commit()



