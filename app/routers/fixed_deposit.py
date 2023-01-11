from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List
import requests
from ..config import settings
from datetime import datetime, timedelta
import uuid


router = APIRouter(
    tags=["Fixed Deposit Accounts"]
)


# version code 7 starts here


# creating a fixed deposit account by user in version Code 7
@router.post("/create_fixed_deposit_account", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupOut)
def user_create_long_term_saving_group(group: schemas.LongTermGroupCreate, db: Session = Depends(get_db),
                             current_user: int = Depends(oauth2.get_current_user)):
    #let us first check whether the user already has a fixed deposit account
    account_check = db.query(models.FixedDepositAccount).filter(models.FixedDepositAccount.user_id == current_user.id).first()

    if account_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You already have a fixed deposit account")

    #let us limit the period to 12 months
    if group.period > 12:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Maximum period to fix your savings is 12 months")


    #let us get payout date for this group
    payout_date = datetime.now() + timedelta(days=30*group.period)
    thisdict = {
        "payout_date": "Ford"

    }
    thisdict["payout_date"] = f"{payout_date}"

    # create group
    new_group = models.FixedDepositAccount(user_id=current_user.id, cycle=1,
                              **thisdict)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return new_group



# specific landing page for fixed deposit account in version code 7
@router.get("/fixed_deposit_landing", response_model=schemas.FixedDepositLandingPage)
def fixed_deposit_landing( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # let us first check whether the user already has a fixed deposit account
    account_check = db.query(models.FixedDepositAccount).filter(
        models.FixedDepositAccount.user_id == current_user.id).first()

    if not account_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not have a fixed deposit account")



    fixed_account_balance = str(account_check.account_balance)

    payout_date = str(account_check.payout_date)

    return {
            "account_balance": fixed_account_balance,
            "payout_date": payout_date
            }




# creating a fixed deposit account payment by user in version code 7
@router.post("/fixed_account_deposit_money", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def fixed_account_deposit_money(payment: schemas.TransactionIn, db: Session = Depends(get_db),
                               current_user: int = Depends(oauth2.get_current_user)):
    # let us first check whether the user already has a fixed deposit account
    account_check = db.query(models.FixedDepositAccount).filter(
        models.FixedDepositAccount.user_id == current_user.id).first()

    if not account_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not have a fixed deposit account")

    # let's check whether payout date has matured. If payout date is matured, do not allow deposits
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    expiry_date_string = str(account_check.payout_date)
    expiry_date_object = datetime.strptime(expiry_date_string, format_string)
    now_string = str(datetime.now())
    now = datetime.strptime(now_string, format_string)
    # maturity_object = now-create_date
    # loan_maturity = maturity_object.days

    if now > expiry_date_object:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"deposits not allowed. Payout date was reached")

    # get old account balance
    old_account_balance = account_check.account_balance

    # get the amount the user wants to deposit
    paymentdict = payment.dict()
    received_deposit = paymentdict["amount"]

    if received_deposit < 1000:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"deposit not allowed. Amount is too little to deposit")


    # add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)




    new_account_balance = old_account_balance + received_deposit

    # register payment
    new_payment = models.FixedDepositTransaction(user_id=current_user.id, account_id=account_check.id,
                                                  amount=payment.amount,
                                                  cycle=account_check.cycle, transaction_type="deposit",
                                                  old_balance=old_account_balance, new_balance=new_account_balance)

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    # use a random dictionary to update the account balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    # update the accout balance of the fixed deposit account
    group_query = db.query(models.FixedDepositAccount).filter(models.FixedDepositAccount.user_id == current_user.id)
    group_query.update(thisdict, synchronize_session=False)
    db.commit()

    # send message to user about balance update
    # lets connect to box-uganda for messaging
    url = "https://boxuganda.com/api.php"
    data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}',
            'sender': 'sambax',
            'message': f'Hello {current_user.first_name}, you have deposited UgX{received_deposit} with Sambax Finance Ltd.Your new Fixed Account balance is UgX{new_account_balance}',
            'reciever': f'{usable_phone_number}'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    test_response = requests.post(url, data=data, headers=headers)
    if test_response.status_code == 200:
        print("message success")


    return new_payment


#creating a withdrawal
@router.post("/fixed_account_withdraw_money", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def fixed_account_withdraw_money(withdraw: schemas.TransactionIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    # let us first check whether the user already has a fixed deposit account
    account_check = db.query(models.FixedDepositAccount).filter(
        models.FixedDepositAccount.user_id == current_user.id).first()

    if not account_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not have a fixed deposit account")

    # let's check whether payout date has matured. If payout date is matured, do not allow deposits
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    expiry_date_string = str(account_check.payout_date)
    expiry_date_object = datetime.strptime(expiry_date_string, format_string)
    now_string = str(datetime.now())
    now = datetime.strptime(now_string, format_string)
    # maturity_object = now-create_date
    # loan_maturity = maturity_object.days

    if now < expiry_date_object:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"withdraws not allowed. Payout date is not yet reached")

    #check whether the user has enough money to withdraw
    withdrawdict = withdraw.dict()
    received_withdraw = withdrawdict["amount"]
    # get old account balance
    old_account_balance = account_check.account_balance

    if received_withdraw < 1500:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"withdraw not allowed. Money is too little to withdraw")

    if received_withdraw > old_account_balance:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"withdraw not allowed. You have less money to withdraw")


    #add logic for collecting money from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)




    #let me try to protect the system until mtn gives us access to their api
    #received_withdraw = 0
    # get new account balance
    new_account_balance = old_account_balance - received_withdraw

    # use a random dictionary to update the account balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_account_balance

    #update the account balance of the user
    account_query = db.query(models.FixedDepositAccount).filter(models.FixedDepositAccount.user_id == current_user.id)
    account_query.update(thisdict, synchronize_session=False)
    db.commit()

    # register withdraw
    #new_withdraw = models.Transaction(user_id=current_user.id, transaction_type="Withdraw",
    #                               old_balance=old_account_balance, new_balance=new_account_balance, **withdraw.dict())
    new_withdraw = models.FixedDepositTransaction(user_id=current_user.id, account_id=account_check.id, transaction_type="Withdraw",
                                      old_balance=old_account_balance, new_balance=new_account_balance,
                                      amount=received_withdraw, made_by="self")
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



#getting all fixed deposit transactions, made by a logged-in user in version code 7
@router.get("/fixed_deposit_transaction_statement", response_model=List[schemas.NormalStatementOutCode6])
def fixed_deposit_transaction_statement(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    transactions = db.query(models.FixedDepositTransaction).filter(models.FixedDepositTransaction.user_id == current_user.id).all()
    return transactions



# Setting a new payout date for a fixed deposit account by user in version Code 7
@router.post("/set_new_payout_date_for_fixed_deposit_account", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupOut)
def set_new_payout_date_for_fixed_deposit_account(group: schemas.LongTermGroupCreate, db: Session = Depends(get_db),
                             current_user: int = Depends(oauth2.get_current_user)):
    # let us first check whether the user already has a fixed deposit account
    account_check = db.query(models.FixedDepositAccount).filter(
        models.FixedDepositAccount.user_id == current_user.id).first()

    if not account_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not have a fixed deposit account")

    # let's check whether payout date has matured. If payout date is matured, and the group account balance is zero, then allow admin to reset payout date
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    expiry_date_string = str(account_check.payout_date)
    expiry_date_object = datetime.strptime(expiry_date_string, format_string)
    now_string = str(datetime.now())
    now = datetime.strptime(now_string, format_string)
    # maturity_object = now-create_date
    # loan_maturity = maturity_object.days

    if now < expiry_date_object:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You can not change payout date now. Current Payout date has not yet expired")


    # let us limit the period to 12 months
    if group.period > 12:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Maximum period to fix your group savings is 12 months")

    # let us update payout date for this group
    payout_date = datetime.now() + timedelta(days=30 * group.period)
    thisdict = {
        "payout_date": "Ford"

    }
    thisdict["payout_date"] = f"{payout_date}"

    group_kologa = db.query(models.FixedDepositAccount).filter(models.FixedDepositAccount.user_id == current_user.id)
    group_kologa.update(thisdict, synchronize_session=False)
    db.commit()

    return account_check




