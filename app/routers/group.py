from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List
import requests
from ..config import settings
from datetime import datetime, timedelta


router = APIRouter(
    tags=["Groups"]
)


#creating a single group
@router.post("/admin/groups", status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    #thisdict = loan.dict()
    #thisdict["expiry_date"] = f"{expiry_date}"
    new_group = models.Group(**group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


#creating a payee for a group
@router.post("/admin/payee", status_code=status.HTTP_201_CREATED, response_model=schemas.PayeeOut)
def create_payee(payee: schemas.PayeeCreate, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    # find the user
    current_user = db.query(models.User).filter(models.User.phone_number == payee.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    #check whether user is already attached to group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id
                                                ).first()

    if current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"user is already attached to a saving group")

    #thisdict = payee.dict()
    #thisdict["user_id"] = f"{current_user.id}"
    cycle_string = payee.cycle
    cycle_upper = cycle_string.upper()

    #new_payee = models.Payee(**thisdict)
    new_payee = models.Payee(week=payee.week_no, group=payee.group_id, user_id=current_user.id, cycle=cycle_upper)
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)
    return new_payee


#creating a group payment by admin
@router.post("/admin/group_payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def create_group_payment_by_admin(payment: schemas.GroupPaymentIn, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    #find the user
    current_user = db.query(models.User).filter(models.User.phone_number == payment.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    #check whether user has a running group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user has no saving group to pay for")



    #add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    #register payment
    new_payment = models.GroupPayment(user_id=current_user.id, group_id=current_payee.group, amount=payment.amount,
                                      week=payment.week, cycle=payment.cycle)

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)


    #get old group balance
    current_group_inquiry = db.query(models.Group).filter(models.Group.id == current_payee.group).first()

    #get new group balance
    paymentdict = payment.dict()
    received_payment = paymentdict["amount"]
    new_group_balance = current_group_inquiry.account_balance + received_payment

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_group_balance

    #update the accout balance of the group
    group_query = db.query(models.Group).filter(models.Group.id == current_payee.group)
    group_query.update(thisdict, synchronize_session=False)
    db.commit()

    #get the other members of the group and message them
    members = db.query(models.Payee).filter(models.Payee.group == current_payee.group).all()

    if not members:
        print("there are no results")

    for member in members:
        user = db.query(models.User).filter(models.User.id == member.user_id).first()

        # send message to user about balance update
        appendage2 = '256'
        number_string2 = str(user.phone_number)
        usable_phone_number_string2 = appendage2 + number_string2
        usable_phone_number2 = int(usable_phone_number_string2)

        # lets connect to box-uganda for messaging
        url = "https://boxuganda.com/api.php"
        data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}',
                'sender': 'sambax',
                'message': f'Hello, {user.first_name},{current_user.first_name} has paid Sambax Finance Ltd UgX{received_payment} for your group savings.Your new group balance UgX{new_group_balance}.',
                'reciever': f'{usable_phone_number2}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")

    return new_payment


#creating a group payment by user
@router.post("/group_payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def create_group_payment_by_user(payment: schemas.GroupPaymentIn, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    #find the user
    current_user = db.query(models.User).filter(models.User.phone_number == payment.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")

    #check whether user has a running group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user has no saving group to pay for")



    #add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    #register payment
    new_payment = models.GroupPayment(user_id=current_user.id, group_id=current_payee.group, amount=payment.amount,
                                      week=payment.week, cycle=payment.cycle)

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)


    #get old group balance
    current_group_inquiry = db.query(models.Group).filter(models.Group.id == current_payee.group).first()

    #get new group balance
    paymentdict = payment.dict()
    received_payment = paymentdict["amount"]
    new_group_balance = current_group_inquiry.account_balance + received_payment

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_group_balance

    #update the accout balance of the group
    group_query = db.query(models.Group).filter(models.Group.id == current_payee.group)
    group_query.update(thisdict, synchronize_session=False)
    db.commit()

    #get the other members of the group and message them
    members = db.query(models.Payee).filter(models.Payee.group == current_payee.group).all()

    if not members:
        print("there are no results")

    for member in members:
        user = db.query(models.User).filter(models.User.id == member.user_id).first()

        # send message to user about balance update
        appendage2 = '256'
        number_string2 = str(user.phone_number)
        usable_phone_number_string2 = appendage2 + number_string2
        usable_phone_number2 = int(usable_phone_number_string2)

        # lets connect to box-uganda for messaging
        url = "https://boxuganda.com/api.php"
        data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}',
                'sender': 'sambax',
                'message': f'Hello, {user.first_name},{current_user.first_name} has paid Sambax Finance Ltd UgX{received_payment} for your group savings.Your new group balance UgX{new_group_balance}.',
                'reciever': f'{usable_phone_number2}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")

    return new_payment

