from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List
import requests
from ..config import settings
from datetime import datetime, timedelta


router = APIRouter(
    tags=["Transactions"]
)

#creating a deposit
@router.post("/deposits", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def create_deposit_by_user(deposit: schemas.TransactionIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #add logic for collecting deposit from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get old account balance
    old_account_balance = current_user.account_balance

    #get new account balance
    depositdict = deposit.dict()
    #received_deposit = depositdict["amount"]
    #let me try to protect our system until mtn gives us access to their api
    received_deposit = 0
    new_account_balance = current_user.account_balance + received_deposit

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    #update the account balance of the user
    account_query = db.query(models.User).filter(models.User.id == current_user.id)
    account_query.update(thisdict, synchronize_session=False)
    db.commit()

    # register deposit
    #new_deposit = models.Transaction(user_id=current_user.id, transaction_type="deposit",
   #                                  old_balance=old_account_balance, new_balance=new_account_balance, **deposit.dict())
    new_deposit = models.Transaction(user_id=current_user.id, transaction_type="deposit",
                                     old_balance=old_account_balance, new_balance=new_account_balance, amount=0,
                                     made_by="self")
    db.add(new_deposit)
    db.commit()
    db.refresh(new_deposit)

    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have deposited UgX{received_deposit} with Sambax Finance Ltd.Your new Account balance is UgX{new_account_balance}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_deposit


#creating a withdrawal
@router.post("/withdrawals", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def create_withdraw_by_user(withdraw: schemas.TransactionIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #add logic for collecting deposit from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get old account balance
    old_account_balance = current_user.account_balance

    #get new account balance
    withdrawdict = withdraw.dict()
    #received_withdraw = withdrawdict["amount"]
    #let me try to protect the system until mtn gives us access to their api
    received_withdraw = 0
    new_account_balance = current_user.account_balance - received_withdraw

    # use a random dictionary to update the account balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    #update the account balance of the user
    account_query = db.query(models.User).filter(models.User.id == current_user.id)
    account_query.update(thisdict, synchronize_session=False)
    db.commit()

    # register withdraw
    #new_withdraw = models.Transaction(user_id=current_user.id, transaction_type="Withdraw",
    #                               old_balance=old_account_balance, new_balance=new_account_balance, **withdraw.dict())
    new_withdraw = models.Transaction(user_id=current_user.id, transaction_type="Withdraw",
                                      old_balance=old_account_balance, new_balance=new_account_balance,
                                      amount=0, made_by="self")
    db.add(new_withdraw)
    db.commit()
    db.refresh(new_withdraw)

    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have withdrawn UgX{received_withdraw} from Sambax Finance Ltd.Your new Account balance is UgX{new_account_balance}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_withdraw


#getting all transactions, made by a logged-in user
@router.get("/transaction_statement", response_model=List[schemas.TransactionOut])
def get_transaction_statement(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()
    return transactions


#creating a deposit by admin
@router.post("/admin/deposits", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def create_deposit_by_admin(deposit: schemas.AdminPayment, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    # find the user
    current_user = db.query(models.User).filter(models.User.phone_number == deposit.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    #add logic for collecting deposit from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get old account balance
    old_account_balance = current_user.account_balance

    #get new account balance
    depositdict = deposit.dict()
    received_deposit = depositdict["amount"]
    new_account_balance = current_user.account_balance + received_deposit

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    #update the account balance of the user
    account_query = db.query(models.User).filter(models.User.id == current_user.id)
    account_query.update(thisdict, synchronize_session=False)
    db.commit()

    # register deposit
    new_deposit = models.Transaction(user_id=current_user.id, transaction_type="deposit", amount=deposit.amount,
                                     old_balance=old_account_balance, new_balance=new_account_balance)
    db.add(new_deposit)
    db.commit()
    db.refresh(new_deposit)

    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have deposited UgX{received_deposit} with Sambax Finance Ltd.Your new Account balance is UgX{new_account_balance}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_deposit


#creating a withdraw by admin
@router.post("/admin/withdraws", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def create_deposit_by_admin(withdraw: schemas.AdminPayment, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    # find the user
    current_user = db.query(models.User).filter(models.User.phone_number == withdraw.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    #add logic for collecting deposit from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get old account balance
    old_account_balance = current_user.account_balance

    #get new account balance
    withdrawdict = withdraw.dict()
    received_withdraw = withdrawdict["amount"]
    new_account_balance = current_user.account_balance - received_withdraw

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    #update the account balance of the user
    account_query = db.query(models.User).filter(models.User.id == current_user.id)
    account_query.update(thisdict, synchronize_session=False)
    db.commit()

    # register withdraw
    new_withdraw = models.Transaction(user_id=current_user.id, transaction_type="withdraw", amount=withdraw.amount,
                                      old_balance=old_account_balance, new_balance=new_account_balance)
    db.add(new_withdraw)
    db.commit()
    db.refresh(new_withdraw)

    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have withdrawn UgX{received_withdraw} from Sambax Finance Ltd.Your new Account balance is UgX{new_account_balance}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_withdraw



#VERSION CODE 6 STARTS HERE
#getting all transactions, made by a logged-in user
@router.get("/normal_statement", response_model=List[schemas.NormalStatementOutCode6])
def get_transaction_statement(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()
    return transactions


#getting total number of deposits, made by admin
@router.get("/admin/total_user_deposits")
def get_total_user_deposits(db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    users = db.query(models.User).all()
    number_of_active_users = len(users)
    sum_account_balance = 0

    for user in users:
        sum_account_balance += user.account_balance


    #sum = loans.with_entities(func.sum(models.Loan.loan_payable)).scalar()
    return number_of_active_users, sum_account_balance


#getting user transaction statement, used by admin
@router.post("/admin/normal_statement", response_model=List[schemas.NormalStatementOutCode6])
def admin_get_transaction_statement(phone_number_given: schemas.PhoneNumberRecover, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    # find the user
    current_user = db.query(models.User).filter(models.User.phone_number == phone_number_given.phone_number).first()

    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()
    return transactions



########VERSION CODE 7 STARTS HERE#########


#making inbound transfers
@router.post("/user_transfer_money", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def user_transfer_money(transfer: schemas.AdminPayment, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    # check the transfer amount and make sure it's not more than the user's account balance
    received_transfer = transfer.amount
    current_account_balance = current_user.account_balance

    if received_transfer > current_account_balance:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have less money to transfer")

    # find the user
    recipient = db.query(models.User).filter(models.User.phone_number == transfer.phone_number).first()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    # now let us perform the transfer of funds
    recipient_old_balance = recipient.account_balance
    print(recipient_old_balance)
    recipient_new_balance = recipient_old_balance + received_transfer
    print(recipient_new_balance)

    #add logic for collecting deposit from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    #get old account balance
    old_account_balance = current_user.account_balance

    #get new account balance
    transferdict = transfer.dict()
    received_transfer = transferdict["amount"]
    #let me try to protect our system until mtn gives us access to their api
    #received_deposit = 0
    new_account_balance = current_user.account_balance + received_transfer

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    #update the account balance of the user
    account_query = db.query(models.User).filter(models.User.id == current_user.id)
    account_query.update(thisdict, synchronize_session=False)
    db.commit()

    # register deposit
    #new_deposit = models.Transaction(user_id=current_user.id, transaction_type="deposit",
   #                                  old_balance=old_account_balance, new_balance=new_account_balance, **deposit.dict())
    new_deposit = models.Transaction(user_id=current_user.id, transaction_type="deposit",
                                     old_balance=old_account_balance, new_balance=new_account_balance, amount=0,
                                     made_by="self")
    db.add(new_deposit)
    db.commit()
    db.refresh(new_deposit)

    #send message to user about balance update
    #lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}', 'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have deposited UgX{received_deposit} with Sambax Finance Ltd.Your new Account balance is UgX{new_account_balance}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")

    return new_deposit
