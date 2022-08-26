from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer

from .database import get_db
from .schemas import TokenData
from sqlalchemy.orm import Session
from .config import settings


#testing timedelta
#@router.get("/testing", status_code=status.HTTP_201_CREATED)
def compound_loan( db: Session = Depends(get_db)):
    #now = datetime.now()
    loans = db.query(models.Loan).filter(models.Loan.running == True).all()
    for loan in loans:
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
            loan_query = db.query(models.Loan).filter(models.Loan.user_id == loan.user_id,
                                                      models.Loan.running == True)
            loan_query.update(thisdict, synchronize_session=False)
            db.commit()



    return {}


db: Session = Depends(get_db)
compound_loan(db)