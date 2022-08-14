from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2
from ..database import engine, get_db
from typing import Optional, List


router = APIRouter(
    tags=["Payments"]
)


#getting all payments, used by admin
@router.get("/payments", response_model=List[schemas.PaymentOut])
def get_payments(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    payments = db.query(models.Payment).all()
    return payments


#getting all payments, made by a logged-in user
@router.get("/mypayments", response_model=List[schemas.PaymentOut])
def get_my_payments(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    payments = db.query(models.Payment).filter(models.Payment.user_id == current_user.id).all()
    return payments


#creating a payment
@router.post("/payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentCreate)
def create_payment(payment: schemas.Payment, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #check whether user has a running loan
    current_loan = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True).first()

    if not current_loan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you have no active loan to pay for")

    #add logic for collecting payment from a user

    #register payment
    new_payment = models.Payment(user_id=current_user.id, loan_id=current_loan.id, **payment.dict())
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    #get new loan balance
    paymentdict = payment.dict()
    received_payment = paymentdict["amount"]
    new_loan_balance = current_loan.loan_balance - received_payment

    # use a random dictionary to update the loan balance
    thisdict = {

        "loan_balance": 1964
    }

    thisdict["loan_balance"] = new_loan_balance

    #update the loan balance of the user
    loan_query = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True)
    loan_query.update(thisdict, synchronize_session=False)
    db.commit()


    return new_payment


#get one payment
@router.get("/payments/{id}", response_model=schemas.PaymentOut)
def get_payment(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    payment = db.query(models.Payment).filter(models.Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"payment with id{id} was not found")

    return payment


#deleting a single payment
@router.delete("/payments/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    payment = db.query(models.Payment).filter(models.Payment.id == id)
    if payment.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"payment with id{id} does not exist")

    payment.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#updating a single payment
@router.put("/payments/{id}", response_model=schemas.PaymentOut)
def update_payment(id: int, payment: schemas.Payment, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    payment_query = db.query(models.Payment).filter(models.Payment.id == id)
    payment_item = payment_query.first()
    if payment_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"payment with id{id} does not exist")

    payment_query.update(payment.dict(), synchronize_session=False)
    db.commit()
    return payment_query.first()

