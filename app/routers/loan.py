from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List
from datetime import datetime


router = APIRouter(
    tags=["Loans"]
)



#getting all loans by admin
@router.get("/admin/loans", response_model=List[schemas.Loan])
def get_loans(db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    loans = db.query(models.Loan).all()
    return loans


#getting a single loan
@router.get("/admin/loans/{id}", response_model=schemas.Loan)
def get_loan(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    loan = db.query(models.Loan).filter(models.Loan.id == id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"loan with id{id} was not found")

    return loan


#creating a single loan
@router.post("/admin/loans", status_code=status.HTTP_201_CREATED, response_model=schemas.Loan)
def create_loan(loan: schemas.LoanCreate, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    #check whether user has a running loan
    current_loan = db.query(models.Loan).filter(models.Loan.user_id == loan.user_id, models.Loan.running == True).first()

    if current_loan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user already has a running loan. you can't create a new loan for them")
    new_loan = models.Loan(**loan.dict())
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan


#deleting a single loan
@router.delete("/admin/loans/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    loan = db.query(models.Loan).filter(models.Loan.id == id)
    if loan.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"loan with id{id} does not exist")

    loan.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#updating a single loan
@router.put("/admin/loans/{id}", response_model=schemas.Loan)
def update_loan(id: int, loan: schemas.LoanCreate, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    loan_query = db.query(models.Loan).filter(models.Loan.id == id)
    loan_item = loan_query.first()
    if loan_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"loan with id{id} does not exist")

    loan_query.update(loan.dict(), synchronize_session=False)
    db.commit()
    return loan_query.first()


#getting loan balance--for user
@router.get("/myloanbalance")
def get_loan_balance( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    current_loan = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True).first()

    if not current_loan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you have no active loan")

    loan_balance = current_loan.loan_balance
    expiry_date = current_loan.expiry_date

    return loan_balance, expiry_date


###############################
#getting loan maturity by admin
@router.post("/admin/loan_maturity")
def get_loan_maturity(given_maturity:schemas.LoanMaturity, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    rvalues = []

    loans = db.query(models.Loan).filter(models.Loan.running == True).all()
    for loan in loans:
        format_string = "%Y-%m-%d %H:%M:%S.%f"
        create_date_string = str(loan.created_at)
        create_date = datetime.strptime(create_date_string, format_string)
        now_string = str(datetime.now())
        now = datetime.strptime(now_string, format_string)
        maturity_object = now-create_date
        loan_maturity = maturity_object.days

        if loan_maturity == given_maturity.sought_maturity :

            #rvalues.append(loan.user_id)
            user = db.query(models.User).filter(models.User.id == loan.user_id).first()
            user_details = [user.first_name, user.last_name, user.phone_number, loan.loan_balance ]
            rvalues.append(user_details)


    return rvalues
#######################################################
