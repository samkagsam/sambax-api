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
    tags=["Long Term Groups"]
)


# version code 7 starts here


# creating a long term group by user in version Code 7
@router.post("/long_term_groups", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupOut)
def user_create_long_term_saving_group(group: schemas.LongTermGroupCreate, db: Session = Depends(get_db),
                             current_user: int = Depends(oauth2.get_current_user)):

    #let us limit the period to 12 months
    if group.period > 12:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Maximum period to fix your group savings is 12 months")

    # let us create a unique id for the new group to be created
    unique_id = uuid.uuid4()

    # print(unique_id)  # 👉️ 011963c3-7fa3-4963-8599-a302f9aefe7d
    # print(type(unique_id))  # 👉️ <class 'uuid.UUID'>

    unique_id_str = str(unique_id)
    # print(unique_id_str)  # 👉️ 011963c3-7fa3-4963-8599-a302f9aefe7d
    # print(type(unique_id_str))  # 👉️ <class 'str'>

    #let us get payout date for this group
    payout_date = datetime.now() + timedelta(days=30*group.period)
    thisdict = {
        "payout_date": "Ford"

    }
    thisdict["payout_date"] = f"{payout_date}"

    # create group
    new_group = models.LongTermGroup(group_admin=current_user.id, cycle=1,
                             identifier=unique_id_str, **thisdict)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # automatically add the creator as the first group member
    # first get the group just created
    creator_group = db.query(models.LongTermGroup).filter(models.LongTermGroup.identifier == unique_id_str).first()
    creator_group_id = creator_group.id

    # add the creator as a payee
    new_payee = models.LongTermGroupMember( group_id=creator_group_id, user_id=current_user.id,
                             approval_status="approved", approval_count=1)
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)

    return new_group


# creating a group member for a long term group by a user admin in version code 7
@router.post("/add_long_term_group_member", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupMemberOut)
def user_add_long_term_group_member(payee: schemas.UserPayeeCreate, db: Session = Depends(get_db),
                            current_user: int = Depends(oauth2.get_current_user)):
    # first check whether user is an admin to this group
    user_group = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == payee.group_id,
                                               models.LongTermGroup.group_admin == current_user.id).first()

    if not user_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"You are not admin to this saving group")

    # get the id of intended payee
    intended_payee = db.query(models.User).filter(models.User.phone_number == payee.phone_number).first()
    if not intended_payee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Phone number is not registered with Sambax Finance")

    # first check whether this intended payee is already an approved member of this group
    payee_inquiry = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == intended_payee.id,
                                                  models.LongTermGroupMember.group_id == user_group.id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).first()

    if payee_inquiry:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user already belongs to this saving group")

    # now check whether the intended payee has already received a group join request
    payee_request = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == intended_payee.id,
                                                  models.LongTermGroupMember.group_id == user_group.id,
                                                  models.LongTermGroupMember.approval_status == "disapproved",
                                                  models.LongTermGroupMember.approval_count == 0).first()
    if payee_request:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"user has already received a group join request for this group")

    # new_payee = models.Payee(**thisdict)
    new_payee = models.LongTermGroupMember( group_id=user_group.id, user_id=intended_payee.id,
                             approval_status="disapproved")
    db.add(new_payee)
    db.commit()
    db.refresh(new_payee)
    return new_payee


# approving group request by user in version code 7
@router.post("/approve_long_term_group_request", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupApprovalRequestOut)
def user_approve_long_term_group_request(id_given: schemas.ApprovalRequestIn, db: Session = Depends(get_db),
                               current_user: int = Depends(oauth2.get_current_user)):
    # first check for the request
    request_inquiry = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == id_given.id).first()

    if not request_inquiry:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You have not received a request to join a group")

    repeat_check = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == id_given.id,
                                                 models.LongTermGroupMember.approval_count == 1).first()

    if repeat_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You have already approved the request")



    # let us now approve the request, use a dictionary to update the request status
    # use a random dictionary to update the loan balance
    # "approval_count": 0
    thisdict = {

        "approval_status": "yyy",
        "approval_count": 0
    }

    thisdict["approval_status"] = "approved"
    thisdict["approval_count"] = 1

    # perform the request approval
    payee_query = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == id_given.id)
    payee_query.update(thisdict, synchronize_session=False)
    db.commit()



    # let us first count the group members
    group_members = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.group_id == request_inquiry.group_id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).all()
    number_of_members = 0
    member_list = []
    for group_member in group_members:
        number_of_members += 1
        member = group_member.user_id
        member_list.append(member)

    print(member_list)


    # let us message all the group members about the new member who has joined
    for group_member in group_members:
        user = db.query(models.User).filter(models.User.id == group_member.user_id).first()

        # send message to user about balance update
        appendage2 = '256'
        number_string2 = str(user.phone_number)
        usable_phone_number_string2 = appendage2 + number_string2
        usable_phone_number2 = int(usable_phone_number_string2)

        # lets connect to box-uganda for messaging
        url = "https://boxuganda.com/api.php"
        data = {'user': f'{settings.box_uganda_username}', 'password': f'{settings.box_uganda_password}',
                'sender': 'sambax',
                'message': f'Hello, {user.first_name},{current_user.first_name}, 0{current_user.phone_number} has joined saving group{request_inquiry.group_id} at Sambax Finance Ltd.',
                'reciever': f'{usable_phone_number2}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")

    return request_inquiry


# disapproving long term group join request in version code 7
@router.post("/disapprove_long_term_group_request", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupApprovalRequestOut)
def user_disapprove_long_term_group_request(id_given: schemas.ApprovalRequestIn, db: Session = Depends(get_db),
                                  current_user: int = Depends(oauth2.get_current_user)):
    # first check for the request
    request_inquiry = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == id_given.id).first()

    if not request_inquiry:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You have not received a request to join a group")

    repeat_check = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == id_given.id,
                                                 models.LongTermGroupMember.approval_count == 1).first()

    if repeat_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You have already disapproved the request")

    # let us now disapprove the request, use a dictionary to update the request status
    # use a random dictionary to update the approval_status and approval count

    thisdict = {

        "approval_status": "yyy",
        "approval_count": 0
    }

    thisdict["approval_status"] = "disapproved"
    thisdict["approval_count"] = 1

    # perform the request approval
    payee_query = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == id_given.id)
    payee_query.update(thisdict, synchronize_session=False)
    db.commit()

    return request_inquiry


# retrieving all long term group join requests by a logged-in user in version code 7
@router.get("/long_term_group_requests", response_model=List[schemas.GroupRequestOut])
def get_long_term_group_requests(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # let us check for requests
    group_requests = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                   models.LongTermGroupMember.approval_status == "disapproved",
                                                   models.LongTermGroupMember.approval_count == 0).all()
    if not group_requests:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have no group join request")

    request_list = []

    for group_request in group_requests:
        given_group = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_request.group_id).first()
        group_admin = given_group.group_admin

        # lets find the credentials of the group admin
        group_admin_credentials = db.query(models.User).filter(models.User.id == group_admin).first()
        admin_first_name = group_admin_credentials.first_name
        admin_last_name = group_admin_credentials.last_name
        admin_phone_number = group_admin_credentials.phone_number
        request_id_string = str(group_request.id)
        group_number_string = str(given_group.id)

        # lets add a zero to the phone number
        appendage = '0'
        number_string = str(admin_phone_number)
        usable_phone_number_string = appendage + number_string

        request_details = {"request_id": request_id_string,
                           "group_number": group_number_string,
                           "admin_first_name": admin_first_name,
                           "admin_last_name": admin_last_name,
                           "admin_phone_number": usable_phone_number_string,

                           }
        request_list.append(request_details)

    return request_list


# retrieving all long term groups by a logged-in user in version code 7
@router.get("/long_term_groups_user_belongs_to", response_model=List[schemas.UserGroupsOut])
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


# specific landing page for group savings in version code 6
@router.post("/group/group_landing_page", response_model=schemas.GroupLandingPage)
def specific_saving_group_landing(id_given: schemas.ApprovalRequestIn, db: Session = Depends(get_db),
                                  current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    group_check = db.query(models.Group).filter(models.Group.id == id_given.id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"saving group with id{id_given.id} does not exist")

    usergroup = str(id_given.id)

    group_payout = str(group_check.payout)
    group_account_balance = str(group_check.account_balance)
    current_week = str(group_check.week)
    current_cycle = str(group_check.cycle)

    # let us get the beneficiary for this week
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


# getting specific group members in version code 6
@router.post("/group/group_members", response_model=List[schemas.AllGroupMembers])
def get_specific_group_members(id_given: schemas.ApprovalRequestIn, db: Session = Depends(get_db),
                               current_user: int = Depends(oauth2.get_current_user)):
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
        # lets add a zero to the phone number
        appendage = '0'
        number_string = str(user.phone_number)
        usable_phone_number_string = appendage + number_string
        # member_details = [user.first_name, user.last_name, usable_phone_number_string]
        # members_list.append(member_details)

        member_details2 = {"first_name": user.first_name,
                           "last_name": user.last_name,
                           "phone_number": usable_phone_number_string,
                           "user_week": user_week,
                           }
        members_list.append(member_details2)

    return members_list


# creating a group payment by user in version code 6
@router.post("/user_group_payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def make_group_payment_by_user(payment: schemas.NewGroupPaymentIn, db: Session = Depends(get_db),
                               current_user: int = Depends(oauth2.get_current_user)):
    # check for the group
    group_check = db.query(models.Group).filter(models.Group.id == payment.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.Payee).filter(models.Payee.user_id == current_user.id,
                                                  models.Payee.group == payment.group_id,
                                                  models.Payee.approval_status == "approved",
                                                  models.Payee.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")

    # let us know the group account balance
    # group_kukebera = db.query(models.Group).filter(models.Group.id == payment.group_id).first()
    current_group_balance = group_check.account_balance
    this_payout = group_check.payout
    money_to_pay = payment.amount
    payment_window = this_payout - current_group_balance

    if money_to_pay > payment_window:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you are paying more money than is required")

    # add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)

    # register payment
    new_payment = models.GroupPayment(user_id=current_user.id, group_id=payment.group_id, amount=payment.amount,
                                      week=group_check.week, cycle=group_check.cycle, transaction_type="deposit")

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    # get old group balance
    current_group_inquiry = db.query(models.Group).filter(models.Group.id == payment.group_id).first()

    # get new group balance
    paymentdict = payment.dict()
    received_payment = paymentdict["amount"]
    new_group_balance = current_group_inquiry.account_balance + received_payment

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_group_balance

    # update the accout balance of the group
    group_query = db.query(models.Group).filter(models.Group.id == current_payee.group)
    group_query.update(thisdict, synchronize_session=False)
    db.commit()

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
                'message': f'Hello, {user.first_name},{current_user.first_name} has paid Sambax Finance Ltd UgX{received_payment} for group{payment.group_id} savings.Your new group balance UgX{new_group_balance}.',
                'reciever': f'{usable_phone_number2}'}
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        test_response = requests.post(url, data=data, headers=headers)
        if test_response.status_code == 200:
            print("message success")

    return new_payment


# creating a withdrawal from group made by user in version code 6
@router.post("/user_group_withdrawal", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def user_create_withdraw_from_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db),
                                    current_user: int = Depends(oauth2.get_current_user)):
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

    # then check whether the user is eligible to withdraw money;  for the user to withdraw:
    # -the user has to be the payee for that week in their saving group
    # -the total amount of payments for that week has to be equal to the payout amount
    # if all conditions are met, allow the user to withdraw, register the withdraw, update the group balance and message all
    # all group members about the withdrawal

    # get group details of user
    # usergroup = current_payee.group
    usergroup = group_given.group_id
    userweek = current_payee.week
    # usercycle = current_payee.cycle
    current_cycle = group_check.cycle
    current_week = group_check.week
    current_cycle_balance = group_check.cycle_balance

    group_details_inquiry = db.query(models.Group).filter(models.Group.id == usergroup).first()
    group_payout = group_details_inquiry.payout
    group_account_balance = group_details_inquiry.account_balance

    # print(usergroup)
    # print(userweek)
    # print(usercycle)
    print(group_payout)

    # check eligibility for withdrawal
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

        # let us update the cycle_balance and group account balance
        new_group_account_balance = 0
        new_cycle_balance = current_cycle_balance + group_payout
        new_week = current_week + 1

        # use a random dictionary to update the account balance
        thisdict = {

            "account_balance": 1964,
            "cycle_balance": 0,
            "week": 0
        }

        thisdict["account_balance"] = new_group_account_balance
        thisdict["cycle_balance"] = new_cycle_balance
        thisdict["week"] = new_week

        # update the account balance and cycle_balance of the group
        group_account_query = db.query(models.Group).filter(models.Group.id == usergroup)
        group_account_query.update(thisdict, synchronize_session=False)
        db.commit()

        # let us now update the week and cycle
        group_dance = db.query(models.Group).filter(models.Group.id == usergroup).first()
        now_cycle_balance = group_dance.cycle_balance
        now_cycle_change = group_dance.cycle_change
        now_cycle = group_dance.cycle

        if now_cycle_balance == now_cycle_change:
            new_cycle_now = now_cycle + 1
            new_week_now = 1
            new_cycle_balance_now = 0

            cycle_week_dict = {

                "cycle_balance": 0,
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


# getting all payments, made to a saving group in version code 6
@router.post("/group_statement", response_model=List[schemas.GroupPaymentsInquiryOut])
def get_all_payments_for_specific_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db),
                                        current_user: int = Depends(oauth2.get_current_user)):
    list_details = []

    # check the group
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"there are no payments for this group this week")

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

        # payment_details.append(user_details)
        list_details.append(user_details2)

    return list_details
