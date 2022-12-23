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
    tags=["Groups"]
)


#creating a single group by admin
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


#creating a group payment by user in version code 5
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


#getting all payments, made to your saving group in version code 5
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


#creating a withdrawal from group made by user in version code 5
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


#creating a withdrawal from group made by admin for version code 5
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


#landing page for group savings for version code 5
@router.get("/group/landing_page", response_model=schemas.GroupLandingPage)
def saving_group_landing( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()
    #usergroup = ""
    #group_payout = ""
    #group_account_balance = ""


    if not current_payee:
        #usergroup = "You do not belong to any saving group"
        #group_payout = "You do not belong to any saving group"
        #group_account_balance = "You do not belong to any saving group"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to any saving group")
    else:
        usergroup = str(current_payee.group)
        group_details_inquiry = db.query(models.Group).filter(models.Group.id == current_payee.group).first()
        group_payout = str(group_details_inquiry.payout)
        group_account_balance = str(group_details_inquiry.account_balance)




    return {"usergroup": usergroup, "group_payout": group_payout, "group_account_balance": group_account_balance}


#getting group members in version code 5
@router.get("/group/members", response_model=List[schemas.GroupMembers])
def get_group_members( db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id).first()

    members_list = []

    if not current_payee:
        members_list = []
        #raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You do not belong to any saving group")


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





#version code 6 starts here




#creating a group by user in version Code 6
@router.post("/groups", status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
def user_create_saving_group(group: schemas.GroupCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #first check whether the user is already a group admin
    #group_inquiry = db.query(models.Group).filter(models.Group.group_admin == current_user.id).first()

    #if group_inquiry:
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You already created a saving group")


    #let us create a unique id for the new group to be created
    unique_id = uuid.uuid4()

    #print(unique_id)  # 👉️ 011963c3-7fa3-4963-8599-a302f9aefe7d
    #print(type(unique_id))  # 👉️ <class 'uuid.UUID'>

    unique_id_str = str(unique_id)
    #print(unique_id_str)  # 👉️ 011963c3-7fa3-4963-8599-a302f9aefe7d
    #print(type(unique_id_str))  # 👉️ <class 'str'>

    #create group
    new_group = models.Group(group_admin=current_user.id, cycle=1, cycle_change=group.payout, week=1,
                             identifier=unique_id_str, **group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    #automatically add the creator as the first payee
    #first get the group just created
    creator_group = db.query(models.Group).filter(models.Group.identifier==unique_id_str).first()
    creator_group_id = creator_group.id

    #add the creator as a payee
    new_payee = models.Payee(week=1, group=creator_group_id, user_id=current_user.id, cycle="A", approval_status="approved",approval_count=1)
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)

    return new_group


#creating a payee for a group by a user admin in version code 6
@router.post("/payees", status_code=status.HTTP_201_CREATED, response_model=schemas.PayeeOut)
def user_create_group_payee(payee: schemas.UserPayeeCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #first get the group where this user is an admin
    user_group = db.query(models.Group).filter(models.Group.group_admin == current_user.id).first()

    if not user_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"You are not admin to any saving group")

    # get the id of intended payee
    intended_payee = db.query(models.User).filter(models.User.phone_number == payee.phone_number).first()
    if not intended_payee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Phone number is not registered with Sambax Finance")


    #first check whether this intended payee is already an approved member of this group
    payee_inquiry = db.query(models.Payee).filter(models.Payee.user_id==intended_payee.id,
                                                  models.Payee.group==user_group.id,
                                                  models.Payee.approval_status == "approved",
                                                  models.Payee.approval_count == 1).first()

    if payee_inquiry:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user already belongs to this saving group")


    #now check whether the intended payee has already received a group join request
    payee_request = db.query(models.Payee).filter(models.Payee.user_id == intended_payee.id,
                                                  models.Payee.group == user_group.id,
                                                  models.Payee.approval_status == "disapproved",
                                                  models.Payee.approval_count == 0).first()
    if payee_request:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user has already received a group join request for this group")

    #new_payee = models.Payee(**thisdict)
    new_payee = models.Payee(week=0, group=user_group.id, user_id=intended_payee.id, cycle="A",
                             approval_status="disapproved")
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)
    return new_payee


#approving group request by user in version code 6
@router.post("/approve_request", status_code=status.HTTP_201_CREATED, response_model=schemas.ApprovalRequestOut)
def user_approve_group_request(id_given:schemas.ApprovalRequestIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #first check for the request
    request_inquiry = db.query(models.Payee).filter(models.Payee.id==id_given.id).first()

    if not request_inquiry:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have not received a request to join a group")

    repeat_check = db.query(models.Payee).filter(models.Payee.id==id_given.id, models.Payee.approval_count==1).first()

    if repeat_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You have already approved the request")

    #let us check whether there's already someone approved for the given week in the given group
    #week_inquiry = db.query(models.Payee).filter(models.Payee.group==request_inquiry.group,
    #                                             models.Payee.week==request_inquiry.week,
    #                                             models.Payee.approval_status=="approved",
    #                                             models.Payee.approval_count==1).first()
    #if week_inquiry:
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
    #                        detail=f"There's already someone assigned to that week")


    #let us now approve the request, use a dictionary to update the request status
    # use a random dictionary to update the loan balance
    #"approval_count": 0
    thisdict = {

        "approval_status": "yyy",
        "approval_count":0
    }

    thisdict["approval_status"] = "approved"
    thisdict["approval_count"] = 1

    # perform the request approval
    payee_query = db.query(models.Payee).filter(models.Payee.id == id_given.id)
    payee_query.update(thisdict, synchronize_session=False)
    db.commit()

    #now let us update cycle change
    #cycle_change = group_payout x no_of_group_members
    #let us first count the group members
    group_members = db.query(models.Payee).filter(models.Payee.group==request_inquiry.group,
                                                  models.Payee.approval_status=="approved",
                                                  models.Payee.approval_count==1).all()
    number_of_members = 0
    member_list = []
    for group_member in group_members:
        number_of_members += 1
        member = group_member.user_id
        member_list.append(member)

    print(member_list)
    position_no = member_list.index(current_user.id)
    week_no = position_no + 1
    print(week_no)

    #let us set the week number for this payee
    weekdict = {

        "week": 0
    }

    weekdict["week"] = week_no
    # perform the week update
    week_query = db.query(models.Payee).filter(models.Payee.id == id_given.id)
    week_query.update(weekdict, synchronize_session=False)
    db.commit()

    #let us find the payout for this group
    group_look = db.query(models.Group).filter(models.Group.id==request_inquiry.group).first()
    current_group_payout = group_look.payout

    new_cycle_change = current_group_payout * number_of_members

    #let us update cycle change with new value using dictionary
    thatdict = {


        "cycle_change": 0
    }


    thatdict["cycle_change"] = new_cycle_change

    # update the cycle change of the group
    group_query = db.query(models.Group).filter(models.Group.id==request_inquiry.group)
    group_query.update(thatdict, synchronize_session=False)
    db.commit()

    #let us message all the group members about the new member who has joined
    for group_member in group_members:
        user = db.query(models.User).filter(models.User.id==group_member.user_id).first()

        # send message to user about balance update
        appendage2 = '256'
        number_string2 = str(user.phone_number)
        usable_phone_number_string2 = appendage2 + number_string2
        usable_phone_number2 = int(usable_phone_number_string2)

        # lets connect to box-uganda for messaging
        url = "https://boxuganda.com/api.php"
        data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}',
                'sender': 'sambax',
                'message': f'Hello, {user.first_name},{current_user.first_name}, 0{current_user.phone_number} has joined saving group{request_inquiry.group} at Sambax Finance Ltd.',
                'reciever': f'{usable_phone_number2}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")



    return request_inquiry


#disapproving group join request in version code 6
@router.post("/disapprove_request", status_code=status.HTTP_201_CREATED, response_model=schemas.ApprovalRequestOut)
def user_disapprove_group_request(id_given:schemas.ApprovalRequestIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #first check for the request
    request_inquiry = db.query(models.Payee).filter(models.Payee.id==id_given.id).first()

    if not request_inquiry:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have not received a request to join a group")

    repeat_check = db.query(models.Payee).filter(models.Payee.id==id_given.id, models.Payee.approval_count==1).first()

    if repeat_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You have already disapproved the request")


    #let us now approve the request, use a dictionary to update the request status
    # use a random dictionary to update the loan balance
    #"approval_count": 0
    thisdict = {

        "approval_status": "yyy",
        "approval_count":0
    }

    thisdict["approval_status"] = "disapproved"
    thisdict["approval_count"] = 1

    # perform the request approval
    payee_query = db.query(models.Payee).filter(models.Payee.id == id_given.id)
    payee_query.update(thisdict, synchronize_session=False)
    db.commit()

    return request_inquiry



#retrieving all group join requests by a logged-in user in version code 6
@router.get("/group_requests", response_model=List[schemas.GroupRequestOut])
def get_group_requests(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    
    # let us check for requests
    group_requests = db.query(models.Payee).filter(models.Payee.user_id == current_user.id,
                                                  models.Payee.approval_status == "disapproved",
                                                  models.Payee.approval_count == 0).all()
    if not group_requests:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have no group join request")

    request_list = []

    for group_request in group_requests:
        given_group = db.query(models.Group).filter(models.Group.id==group_request.group).first()
        group_admin = given_group.group_admin

        #lets find the credentials of the group admin
        group_admin_credentials = db.query(models.User).filter(models.User.id==group_admin).first()
        admin_first_name = group_admin_credentials.first_name
        admin_last_name = group_admin_credentials.last_name
        admin_phone_number = group_admin_credentials.phone_number
        request_id_string = str(group_request.id)
        group_number_string = str(given_group.id)

        # lets add a zero to the phone number
        appendage = '0'
        number_string = str(admin_phone_number)
        usable_phone_number_string = appendage + number_string

        request_details = {"request_id":request_id_string,
                           "group_number":group_number_string,
                           "admin_first_name": admin_first_name,
                           "admin_last_name": admin_last_name,
                           "admin_phone_number": usable_phone_number_string,

                           }
        request_list.append(request_details)

    return request_list


# retrieving all groups by a logged-in user in version code 6
@router.get("/groups_user_belongs_to", response_model=List[schemas.UserGroupsOut])
def get_groups_user_belongs_to(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # let us check for requests
    group_checks = db.query(models.Payee).filter(models.Payee.user_id == current_user.id,
                                                   models.Payee.approval_status == "approved",
                                                   models.Payee.approval_count == 1).all()
    if not group_checks:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have no saving group")

    group_credentials = []
    for group_check in group_checks:
        group_detail = {"id": group_check.group,

                           }
        group_credentials.append(group_detail)
    return group_credentials


#specific landing page for group savings in version code 6
@router.post("/group/group_landing_page", response_model=schemas.GroupLandingPage)
def specific_saving_group_landing(id_given:schemas.ApprovalRequestIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    group_check = db.query(models.Group).filter(models.Group.id == id_given.id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group with id{id_given.id} does not exist")

    usergroup = str(id_given.id)

    group_payout = str(group_check.payout)
    group_account_balance = str(group_check.account_balance)
    current_week = str(group_check.week)
    current_cycle = str(group_check.cycle)

    #let us get the beneficiary for this week
    payee_inquiry = db.query(models.Payee).filter(models.Payee.group == id_given.id,
                                                  models.Payee.week == group_check.week,
                                                  models.Payee.approval_status == "approved",
                                                  models.Payee.approval_count == 1).first()
    payee_id = payee_inquiry.user_id

    current_payee = db.query(models.User).filter(models.User.id == payee_id).first()
    week_beneficiary = current_payee.first_name + " " + current_payee.last_name

    return {"usergroup": usergroup,
            "group_payout": group_payout,
            "group_account_balance": group_account_balance,
            "current_week": current_week,
            "current_cycle": current_cycle,
            "week_beneficiary": week_beneficiary}


#getting specific group members in version code 6
@router.post("/group/group_members", response_model=List[schemas.AllGroupMembers])
def get_specific_group_members(id_given:schemas.ApprovalRequestIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # check the saving group
    group_check = db.query(models.Group).filter(models.Group.id == id_given.id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"saving group with id{id_given.id} does not exist")



    members_list = []

    # get the members of the group
    members = db.query(models.Payee).filter(models.Payee.group == id_given.id,
                                            models.Payee.approval_status == "approved",
                                            models.Payee.approval_count == 1).all()
    for member in members:
        user_week = member.week
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
                           "user_week": user_week,
                         }
        members_list.append(member_details2)

    return members_list


#creating a group payment by user in version code 6
@router.post("/user_group_payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def make_group_payment_by_user(payment: schemas.NewGroupPaymentIn, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #check for the group
    group_check = db.query(models.Group).filter(models.Group.id == payment.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    #check whether user belongs to this group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id,
                                                  models.Payee.group == payment.group_id,
                                                  models.Payee.approval_status == "approved",
                                                  models.Payee.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")



    #let us know the group account balance
    #group_kukebera = db.query(models.Group).filter(models.Group.id == payment.group_id).first()
    current_group_balance = group_check.account_balance
    this_payout = group_check.payout
    money_to_pay = payment.amount
    payment_window = this_payout - current_group_balance

    if money_to_pay > payment_window:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you are paying more money than is required")

    #add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    #register payment
    new_payment = models.GroupPayment(user_id=current_user.id, group_id=payment.group_id, amount=payment.amount,
                                      week=group_check.week, cycle=group_check.cycle, transaction_type="deposit")

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)


    #get old group balance
    current_group_inquiry = db.query(models.Group).filter(models.Group.id == payment.group_id).first()

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
    members = db.query(models.Payee).filter(models.Payee.group == current_payee.group,
                                            models.Payee.approval_status == "approved",
                                            models.Payee.approval_count == 1).all()

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
                'message': f'Hello, {user.first_name},{current_user.first_name} has paid Sambax Finance Ltd UgX{received_payment} for group{payment.group_id} savings.Your new group balance UgX{new_group_balance}.',
                'reciever': f'{usable_phone_number2}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")

    return new_payment


#creating a withdrawal from group made by user in version code 6
@router.post("/user_group_withdrawal", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def user_create_withdraw_from_group(group_given:schemas.NewGroupWithdraw, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # check for the group
    group_check = db.query(models.Group).filter(models.Group.id == group_given.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id,
                                                  models.Payee.group == group_given.group_id,
                                                  models.Payee.approval_status == "approved",
                                                  models.Payee.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")


    #then check whether the user is eligible to withdraw money;  for the user to withdraw:
              #-the user has to be the payee for that week in their saving group
              #-the total amount of payments for that week has to be equal to the payout amount
    #if all conditions are met, allow the user to withdraw, register the withdraw, update the group balance and message all
    #all group members about the withdrawal



    #get group details of user
    #usergroup = current_payee.group
    usergroup = group_given.group_id
    userweek = current_payee.week
    #usercycle = current_payee.cycle
    current_cycle = group_check.cycle
    current_week = group_check.week
    current_cycle_balance = group_check.cycle_balance

    group_details_inquiry = db.query(models.Group).filter(models.Group.id == usergroup).first()
    group_payout = group_details_inquiry.payout
    group_account_balance = group_details_inquiry.account_balance

    #print(usergroup)
    #print(userweek)
    #print(usercycle)
    print(group_payout)


    #check eligibility for withdrawal
    if group_payout == group_account_balance and current_week == userweek:
        # add logic for sending money to the current user
        appendage = '256'
        number_string = str(current_user.phone_number)
        usable_phone_number_string = appendage + number_string
        usable_phone_number = int(usable_phone_number_string)

        # register withdraw
        new_withdraw = models.GroupPayment(user_id=current_user.id, group_id=usergroup, amount=group_payout,
                                           week=current_week, cycle=current_cycle, transaction_type="withdraw")
        db.add(new_withdraw)
        db.commit()
        db.refresh(new_withdraw)

        #let us update the cycle_balance and group account balance
        new_group_account_balance = 0
        new_cycle_balance = current_cycle_balance + group_payout
        new_week = current_week + 1

        # use a random dictionary to update the account balance
        thisdict = {

            "account_balance": 1964,
            "cycle_balance": 0,
            "week":0
        }

        thisdict["account_balance"] = new_group_account_balance
        thisdict["cycle_balance"] = new_cycle_balance
        thisdict["week"] = new_week

        # update the account balance and cycle_balance of the group
        group_account_query = db.query(models.Group).filter(models.Group.id == usergroup)
        group_account_query.update(thisdict, synchronize_session=False)
        db.commit()

        #let us now update the week and cycle
        group_dance = db.query(models.Group).filter(models.Group.id == usergroup).first()
        now_cycle_balance = group_dance.cycle_balance
        now_cycle_change = group_dance.cycle_change
        now_cycle = group_dance.cycle


        if now_cycle_balance == now_cycle_change:
            new_cycle_now = now_cycle + 1
            new_week_now = 1
            new_cycle_balance_now = 0

            cycle_week_dict = {

                "cycle_balance":0,
                "cycle": 1964,
                "week": 0
            }

            cycle_week_dict["cycle_balance"] = new_cycle_balance_now
            cycle_week_dict["cycle"] = new_cycle_now
            cycle_week_dict["week"] = new_week_now

            group_kologa = db.query(models.Group).filter(models.Group.id == usergroup)
            group_kologa.update(cycle_week_dict, synchronize_session=False)
            db.commit()

        # send message to all group members about group balance update
        # get the other members of the group and message them
        members = db.query(models.Payee).filter(models.Payee.group == current_payee.group,
                                                models.Payee.approval_status == "approved",
                                                models.Payee.approval_count == 1).all()

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
                    'message': f'Hello, {user.first_name},{current_user.first_name} has withdrawn UgX{group_payout} from your group{group_given.group_id} savings at Sambax Finance Ltd.Your new group balance UgX{new_group_account_balance}.',
                    'reciever': f'{usable_phone_number2}'}
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            test_response = requests.post(url, data=data, headers=headers)
            if test_response.status_code == 200:
                print("message success")

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"withdrawal not allowed")

    return new_withdraw


#getting all payments, made to a saving group in version code 6
@router.post("/group_statement", response_model=List[schemas.GroupPaymentsInquiryOut])
def get_all_payments_for_specific_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    list_details = []

    #check the group
    group_check = db.query(models.Group).filter(models.Group.id == group_given.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id,
                                                  models.Payee.group == group_given.group_id,
                                                  models.Payee.approval_status == "approved",
                                                  models.Payee.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")



    payments = db.query(models.GroupPayment).filter(models.GroupPayment.group_id == group_given.group_id,
                                                    models.GroupPayment.cycle == str(group_check.cycle),
                                                    models.GroupPayment.week == group_check.week).all()
    if not payments:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"there are no payments for this group this week")

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
