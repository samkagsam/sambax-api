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
def create_group_payment_by_admin(payment: schemas.AdminGroupPaymentIn, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
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
                                      week=payment.week, cycle=payment.cycle, transaction_type="deposit")

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
def create_group_payment_by_user(payment: schemas.GroupPaymentIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

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
                                      week=payment.week, cycle=payment.cycle, transaction_type="deposit")

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


#getting all payments, made to your saving group
#@router.get("/group/payments", response_model=List[schemas.PaymentOut])
@router.post("/group/payments", response_model=List[schemas.GroupPaymentsInquiryOut])
def get_my_group_payments(cycle_given: schemas.GroupPaymentsInquiry, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #payment_details = []
    list_details = []
    #payments = db.query(models.Payment).filter(models.Payment.user_id == current_user.id).all()
    payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    if not payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user has no saving group to inquire for")

    payments = db.query(models.GroupPayment).filter(models.GroupPayment.group_id == payee.group,
                                                    models.GroupPayment.cycle == cycle_given.cycle,
                                                    models.GroupPayment.week == cycle_given.week).all()

    for payment in payments:
        user = db.query(models.User).filter(models.User.id == payment.user_id).first()

        # lets add a zero to the phone number
        appendage = '0'
        number_string = str(user.phone_number)
        usable_phone_number_string = appendage + number_string

        user_details2 = {"first_name": user.first_name,
                         "last_name": user.last_name,
                         "phone_number": usable_phone_number_string,
                         "amount": payment.amount,
                         "created_at": payment.created_at}

        #payment_details.append(user_details)
        list_details.append(user_details2)

    return list_details


#creating a withdrawal from group made by user
@router.get("/group/withdrawals", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def create_withdraw_from_group_by_user(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #first of check whether the user belongs to any saving group
    #then check whether the user is eligible to withdraw money;  for the user to withdraw:
              #-the user has to be the payee for that week in their saving group
              #-the total amount of payments for that week has to be equal to the payout amount
    #if all conditions are met, allow the user to withdraw, register the withdraw, update the group balance and message all
    #all group members about the withdrawal

    #get the saving group of the user
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to any saving group")

    #get group details of user
    usergroup = current_payee.group
    userweek = current_payee.week
    usercycle = current_payee.cycle
    group_details_inquiry = db.query(models.Group).filter(models.Group.id == usergroup).first()
    group_payout = group_details_inquiry.payout
    group_account_balance = group_details_inquiry.account_balance

    #print(usergroup)
    #print(userweek)
    #print(usercycle)
    print(group_payout)


    # check in group payments and see whether the user's payout week has been fully paid for
    # to do this, first get the total number of payments made to the user's payout week
    payments = db.query(models.GroupPayment).filter(models.GroupPayment.group_id == usergroup,
                                                                     models.GroupPayment.week == userweek,
                                                                     models.GroupPayment.cycle == usercycle,
                                                                     models.GroupPayment.transaction_type == "deposit").all()
    if not payments:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Withdrawal not allowed")

    sum_payments = 0
    for payment in payments:
        sum_payments += payment.amount

    print(sum_payments)

    if sum_payments < group_payout:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Payments less than payout.Withdrawal not allowed")

    if group_account_balance < group_payout:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Insufficient group balance.Withdrawal not allowed")

    if sum_payments >= group_payout:
        # add logic for collecting deposit from a user
        appendage = '256'
        number_string = str(current_user.phone_number)
        usable_phone_number_string = appendage + number_string
        usable_phone_number = int(usable_phone_number_string)

        # register withdraw
        new_withdraw = models.GroupPayment(user_id=current_user.id, group_id=usergroup, amount=group_payout,
                                          week=userweek, cycle=usercycle, transaction_type="withdraw")
        db.add(new_withdraw)
        db.commit()
        db.refresh(new_withdraw)

        # get new group account balance
        new_group_account_balance = group_account_balance - group_payout

        # use a random dictionary to update the account balance
        thisdict = {

            "account_balance": 1964
        }

        thisdict["account_balance"] = new_group_account_balance

        # update the account balance of the group
        group_account_query = db.query(models.Group).filter(models.Group.id == usergroup)
        group_account_query.update(thisdict, synchronize_session=False)
        db.commit()

        # send message to all group members about group balance update
        # get the other members of the group and message them
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
                    'message': f'Hello, {user.first_name},{current_user.first_name} has withdrawn UgX{group_payout} from your group savings at Sambax Finance Ltd.Your new group balance UgX{new_group_account_balance}.',
                    'reciever': f'{usable_phone_number2}'}
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            test_response = requests.post(url, data=data, headers=headers)
            if test_response.status_code == 200:
                print("message success")

    return new_withdraw


#creating a withdrawal from group made by admin
@router.post("/admin/group/withdrawals", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def create_withdraw_from_group_by_admin(withdraw_inquirer: schemas.PhoneNumberRecover, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    # find the user
    current_user = db.query(models.User).filter(models.User.phone_number == withdraw_inquirer.phone_number).first()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with that phone number was not found")
    #first of check whether the user belongs to any saving group
    #then check whether the user is eligible to withdraw money;  for the user to withdraw:
              #-the user has to be the payee for that week in their saving group
              #-the total amount of payments for that week has to be equal to the payout amount
    #if all conditions are met, allow the user to withdraw, register the withdraw, update the group balance and message all
    #all group members about the withdrawal

    #get the saving group of the user
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to any saving group")

    #get group details of user
    usergroup = current_payee.group
    userweek = current_payee.week
    usercycle = current_payee.cycle
    group_details_inquiry = db.query(models.Group).filter(models.Group.id == usergroup).first()
    group_payout = group_details_inquiry.payout
    group_account_balance = group_details_inquiry.account_balance

    #print(usergroup)
    #print(userweek)
    #print(usercycle)
    print(group_payout)


    # check in group payments and see whether the user's payout week has been fully paid for
    # to do this, first get the total number of payments made to the user's payout week
    payments = db.query(models.GroupPayment).filter(models.GroupPayment.group_id == usergroup,
                                                                     models.GroupPayment.week == userweek,
                                                                     models.GroupPayment.cycle == usercycle,
                                                                     models.GroupPayment.transaction_type == "deposit").all()
    if not payments:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Withdrawal not allowed")

    sum_payments = 0
    for payment in payments:
        sum_payments += payment.amount

    print(sum_payments)

    if sum_payments < group_payout:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Payments less than payout.Withdrawal not allowed")

    if group_account_balance < group_payout:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Insufficient group balance.Withdrawal not allowed")

    if sum_payments >= group_payout:
        # add logic for collecting deposit from a user
        appendage = '256'
        number_string = str(current_user.phone_number)
        usable_phone_number_string = appendage + number_string
        usable_phone_number = int(usable_phone_number_string)

        # register withdraw
        new_withdraw = models.GroupPayment(user_id=current_user.id, group_id=usergroup, amount=group_payout,
                                          week=userweek, cycle=usercycle, transaction_type="withdraw")
        db.add(new_withdraw)
        db.commit()
        db.refresh(new_withdraw)

        # get new group account balance
        new_group_account_balance = group_account_balance - group_payout

        # use a random dictionary to update the account balance
        thisdict = {

            "account_balance": 1964
        }

        thisdict["account_balance"] = new_group_account_balance

        # update the account balance of the group
        group_account_query = db.query(models.Group).filter(models.Group.id == usergroup)
        group_account_query.update(thisdict, synchronize_session=False)
        db.commit()

        # send message to all group members about group balance update
        # get the other members of the group and message them
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
                    'message': f'Hello, {user.first_name},{current_user.first_name} has withdrawn UgX{group_payout} from your group savings at Sambax Finance Ltd.Your new group balance UgX{new_group_account_balance}.',
                    'reciever': f'{usable_phone_number2}'}
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            test_response = requests.post(url, data=data, headers=headers)
            if test_response.status_code == 200:
                print("message success")

    return new_withdraw


#landing page for group savings
@router.get("/group/landing_page", response_model=schemas.GroupLandingPage)
def saving_group_landing( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()
    usergroup = ""
    group_payout = ""
    group_account_balance = ""


    if not current_payee:
        usergroup = "You do not belong to any saving group"
        group_payout = "You do not belong to any saving group"
        group_account_balance = "You do not belong to any saving group"
        #raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to any saving group")
    else:
        usergroup = str(current_payee.group)
        group_details_inquiry = db.query(models.Group).filter(models.Group.id == current_payee.group).first()
        group_payout = str(group_details_inquiry.payout)
        group_account_balance = str(group_details_inquiry.account_balance)




    return {"usergroup": usergroup, "group_payout": group_payout, "group_account_balance": group_account_balance}


#getting group members
@router.get("/group/members", response_model=List[schemas.GroupMembers])
def get_group_members( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    members_list = []

    if not current_payee:

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not belong to any saving group")
    else:
        # get the members of the group
        members = db.query(models.Payee).filter(models.Payee.group == current_payee.group).all()
        for member in members:
            user = db.query(models.User).filter(models.User.id == member.user_id).first()
            #lets add a zero to the phone number
            appendage = '0'
            number_string = str(user.phone_number)
            usable_phone_number_string = appendage + number_string
            #member_details = [user.first_name, user.last_name, usable_phone_number_string]
            #members_list.append(member_details)

            member_details2 = {"first_name": user.first_name,
                             "last_name": user.last_name,
                             "phone_number": usable_phone_number_string,
                             }
            members_list.append(member_details2)

    return members_list
