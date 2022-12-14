from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List
import requests
from ..config import settings
from datetime import datetime, timedelta


router = APIRouter(
    tags=["Payments"]
)


#getting all payments, used by admin
@router.get("/admin/payments", response_model=List[schemas.PaymentOut])
def get_payments(db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    payments = db.query(models.Payment).all()
    return payments


#getting all payments, made by a logged-in user
@router.get("/mypayments", response_model=List[schemas.PaymentOut])
def get_my_payments(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    payments = db.query(models.Payment).filter(models.Payment.user_id == current_user.id).all()
    return payments


#creating a payment
@router.post("/payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def create_payment_by_user(payment: schemas.Payment, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #check whether user has a running loan
    current_loan = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True).first()

    if not current_loan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you have no active loan to pay for")

    #let us not deduct more money than the loan current loan balance
    money_to_pay_dict = payment.dict()
    money_to_pay = money_to_pay_dict["amount"]
    if money_to_pay > current_loan.loan_balance:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"the amount you are trying to pay is more than your loan balance")

    #add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get old loan balance
    old_loan_balance = current_loan.loan_balance

    #get new loan balance
    paymentdict = payment.dict()
    #received_payment = paymentdict["amount"]
    #let me try to protect transaction until mtn gives us api access
    received_payment = 0
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

    # register payment
    #new_payment = models.Payment(user_id=current_user.id, loan_id=current_loan.id, **payment.dict(),
    #                             old_balance=old_loan_balance, new_balance=new_loan_balance)
    new_payment = models.Payment(user_id=current_user.id, loan_id=current_loan.id, amount=0,
                                 old_balance=old_loan_balance, new_balance=new_loan_balance,
                                 transaction_type="debit", made_by="self")
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    #turn off the loan if the loan balance of the current user is zero
    loan_off_query = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True, models.Loan.loan_balance == 0)
    loan_for_turn_off = loan_off_query.first()
    if loan_for_turn_off is not None:
        loan_off_dict = {
            "running": False
        }
        loan_off_query.update(loan_off_dict, synchronize_session=False)
        db.commit()




    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have paid Sambax Finance UgX{received_payment}.Your loan balance UgX{new_loan_balance}. your loan expiry date is {current_loan.expiry_date}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_payment


#get one payment by admin
@router.get("/admin/payments/{id}", response_model=schemas.PaymentOut)
def get_payment(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    payment = db.query(models.Payment).filter(models.Payment.id == id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"payment with id{id} was not found")

    return payment


#deleting a single payment by admin
@router.delete("/admin/payments/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    payment = db.query(models.Payment).filter(models.Payment.id == id)
    if payment.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"payment with id{id} does not exist")

    payment.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#updating a single payment by admin
@router.put("/admin/payments/{id}", response_model=schemas.PaymentOut)
def update_payment(id: int, payment: schemas.Payment, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    payment_query = db.query(models.Payment).filter(models.Payment.id == id)
    payment_item = payment_query.first()
    if payment_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"payment with id{id} does not exist")

    payment_query.update(payment.dict(), synchronize_session=False)
    db.commit()
    return payment_query.first()


#creating a payment by admin
@router.post("/admin/payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def create_payment_by_admin(payment: schemas.AdminPayment, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    #find the user
    current_user = db.query(models.User).filter(models.User.phone_number == payment.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    #check whether user has a running loan
    current_loan = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True).first()

    if not current_loan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user has no active loan to pay for")

    #let us not deduct more money than the loan current loan balance
    money_to_pay_dict = payment.dict()
    money_to_pay = money_to_pay_dict["amount"]
    if money_to_pay > current_loan.loan_balance:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"the amount you are trying to pay is more than the users loan balance")

    #add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get new loan balance
    old_loan_balance = current_loan.loan_balance
    #print(old_loan_balance)
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

    # register payment
    new_payment = models.Payment(user_id=current_user.id, loan_id=current_loan.id, amount=payment.amount,
                                 old_balance=old_loan_balance, new_balance=new_loan_balance,
                                 transaction_type="debit", made_by="admin")
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    #turn off the loan if the loan balance of the current user is zero
    loan_off_query = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True, models.Loan.loan_balance == 0)
    loan_for_turn_off = loan_off_query.first()
    if loan_for_turn_off is not None:
        loan_off_dict = {
            "running": False
        }
        loan_off_query.update(loan_off_dict, synchronize_session=False)
        db.commit()

    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have paid Sambax Finance UgX{received_payment}.Your loan balance UgX{new_loan_balance}. your loan expiry date is {current_loan.expiry_date}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_payment


# getting the total number of  payments received in a timeframe, used by admin
@router.post("/admin/number_of_payments_made_in_timeframe")
def get_payments_made(received_dates: schemas.ReceivedDates, db: Session = Depends(get_db),
                     current_admin: int = Depends(admin_oauth2.get_current_admin)):
    payments = db.query(models.Payment).all()
    # number_of_active_loans = len(loans)
    num_payments_made = 0
    sum_payments_made = 0
    for payment in payments:

        # print("hello")
        format_string = "%Y-%m-%d %H:%M:%S.%f"
        create_date_string = str(payment.created_at)
        create_date_object = datetime.strptime(create_date_string, format_string)

        # from_date_string = "2022-08-01 00:00:00.000000"
        # to_date_string = "2022-08-31 00:00:00.00000"
        from_date_string = received_dates.from_date
        to_date_string = received_dates.to_date
        from_date_object = datetime.strptime(from_date_string, format_string)
        to_date_object = datetime.strptime(to_date_string, format_string)

        if from_date_object <= create_date_object <= to_date_object:
            # print("hehe")
            # print(create_date_object)

            # get the number of loans issued
            num_payments_made += 1
            sum_payments_made += payment.amount

    return num_payments_made, sum_payments_made


#getting all payments, made by a user, used by admin
@router.post("/admin/user_payments", response_model=List[schemas.PaymentOut])
def get_user_payments(phone_number_given: schemas.PhoneNumberRecover, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    # find the user
    current_user = db.query(models.User).filter(models.User.phone_number == phone_number_given.phone_number).first()

    payments = db.query(models.Payment).filter(models.Payment.user_id == current_user.id).all()
    return payments


#VERSION CODE 6 STARTS HERE

#getting all payments, made by a logged-in user in version code 6
@router.get("/myloanstatement", response_model=List[schemas.LoanStatementOutCode6])
def get_my_loan_statement(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    payments = db.query(models.Payment).filter(models.Payment.user_id == current_user.id).all()
    return payments