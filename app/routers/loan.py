from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.sql import func


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
    expiry_date = datetime.now() + timedelta(days=loan.loan_period)
    thisdict = loan.dict()
    thisdict["expiry_date"] = f"{expiry_date}"
    new_loan = models.Loan(**thisdict)
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


#getting the total number of active loans by admin
@router.get("/admin/total_number_of_active_loans")
def get_loans_statistics(db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    loans = db.query(models.Loan).filter(models.Loan.running == True).all()
    number_of_active_loans = len(loans)
    sum_loans_payable = 0
    sum_loans_balance = 0
    for loan in loans:
        sum_loans_payable += loan.loan_payable
        sum_loans_balance += loan.loan_balance

    #sum = loans.with_entities(func.sum(models.Loan.loan_payable)).scalar()
    return number_of_active_loans, sum_loans_payable, sum_loans_balance


#getting the total number of  loans issued in a timeframe by admin
@router.post("/admin/number_of_loans_issued_in_timeframe")
def get_loans_issued(received_dates:schemas.ReceivedDates, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    loans = db.query(models.Loan).all()
    #number_of_active_loans = len(loans)
    num_loans_issued = 0
    sum_loan_principle = 0
    sum_loan_interest = 0
    for loan in loans:


        #print("hello")
        format_string = "%Y-%m-%d %H:%M:%S.%f"
        create_date_string = str(loan.created_at)
        create_date_object = datetime.strptime(create_date_string, format_string)

        #from_date_string = "2022-08-01 00:00:00.000000"
        #to_date_string = "2022-08-31 00:00:00.00000"
        from_date_string = received_dates.from_date
        to_date_string = received_dates.to_date
        from_date_object = datetime.strptime(from_date_string, format_string)
        to_date_object = datetime.strptime(to_date_string, format_string)



        if from_date_object <= create_date_object <= to_date_object:
            #print("hehe")
            #print(create_date_object)

            #get the number of loans issued
            num_loans_issued += 1
            sum_loan_principle += loan.loan_principle
            sum_loan_interest += loan.loan_interest



    return num_loans_issued, sum_loan_principle, sum_loan_interest


#get expired loans, used by admin
@router.get("/admin/expired_loans")
def get_expired_loans(db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    loan_details = []
    loans = db.query(models.Loan).filter(models.Loan.running == True).all()

    if not loans:
        print("there are no results")
    for loan in loans:
        #print("hello")
        format_string = "%Y-%m-%d %H:%M:%S.%f"
        expiry_date_string = str(loan.expiry_date)
        expiry_date_object = datetime.strptime(expiry_date_string, format_string)
        now_string = str(datetime.now())
        now = datetime.strptime(now_string, format_string)
        #maturity_object = now-create_date
        #loan_maturity = maturity_object.days

        if now > expiry_date_object :
            #rvalues.append(loan.user_id)
            user = db.query(models.User).filter(models.User.id == loan.user_id).first()
            user_details = [user.first_name, user.last_name, user.phone_number, loan.loan_balance ]
            loan_details.append(user_details)

    return loan_details

