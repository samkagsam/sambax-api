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
def get_long_term_groups_user_belongs_to(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # let us check for requests
    group_checks = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                 models.LongTermGroupMember.approval_status == "approved",
                                                 models.LongTermGroupMember.approval_count == 1).all()
    if not group_checks:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You have no saving group")

    group_credentials = []
    for group_check in group_checks:
        group_detail = {"id": group_check.group_id,

                        }
        group_credentials.append(group_detail)
    return group_credentials


# specific landing page for long term savings group in version code 7
@router.post("/specific_long_term_saving_group_landing", response_model=schemas.LongTermGroupLandingPage)
def specific_long_term_saving_group_landing(id_given: schemas.ApprovalRequestIn, db: Session = Depends(get_db),
                                  current_user: int = Depends(oauth2.get_current_user)):
    # get the saving group of the user
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == id_given.id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"saving group with id{id_given.id} does not exist")

    usergroup = str(id_given.id)


    group_account_balance = str(group_check.account_balance)
    current_cycle = str(group_check.cycle)
    payout_date = str(group_check.payout_date)

    return {"usergroup": usergroup,
            "group_account_balance": group_account_balance,
            "current_cycle": current_cycle,
            "payout_date": payout_date,
            }


# getting specific long term group members in version code 7
@router.post("/see_long_term_group_members", response_model=List[schemas.SeeLongTermGroupMembers])
def get_specific_long_term_group_members(id_given: schemas.ApprovalRequestIn, db: Session = Depends(get_db),
                               current_user: int = Depends(oauth2.get_current_user)):
    # check the saving group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == id_given.id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"saving group with id{id_given.id} does not exist")

    members_list = []

    # get the members of the group
    members = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.group_id == id_given.id,
                                            models.LongTermGroupMember.approval_status == "approved",
                                            models.LongTermGroupMember.approval_count == 1).all()
    for member in members:

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

                           }
        members_list.append(member_details2)

    return members_list


# creating a long term group payment by user in version code 7
@router.post("/user_long_term_group_payments", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def make_long_term_group_payment_by_user(payment: schemas.NewGroupPaymentIn, db: Session = Depends(get_db),
                               current_user: int = Depends(oauth2.get_current_user)):
    # check for the group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == payment.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                  models.LongTermGroupMember.group_id == payment.group_id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")

    # let's check whether payout date has matured. If payout date is matured, do not allow deposits
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    expiry_date_string = str(group_check.payout_date)
    expiry_date_object = datetime.strptime(expiry_date_string, format_string)
    now_string = str(datetime.now())
    now = datetime.strptime(now_string, format_string)
    # maturity_object = now-create_date
    # loan_maturity = maturity_object.days

    if now > expiry_date_object:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"deposits not allowed. Payout date was reached")


    # add logic for collecting payment from a user
    appendage = '256'
    number_string = str(current_user.phone_number)
    usable_phone_number_string = appendage + number_string
    usable_phone_number = int(usable_phone_number_string)



    # get old group balance
    current_group_inquiry = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == payment.group_id).first()
    old_group_balance = current_group_inquiry.account_balance

    # get new group balance
    paymentdict = payment.dict()
    received_payment = paymentdict["amount"]
    new_group_balance = old_group_balance + received_payment

    # register payment
    new_payment = models.LongTermGroupTransaction(user_id=current_user.id, group_id=payment.group_id,
                                                  amount=payment.amount,
                                                  cycle=group_check.cycle, transaction_type="deposit",
                                                  old_balance=old_group_balance, new_balance=new_group_balance)

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    # use a random dictionary to update the loan balance
    thisdict = {

        "account_balance": 1964
    }

    thisdict["account_balance"] = new_group_balance

    # update the accout balance of the group
    group_query = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == current_payee.group_id)
    group_query.update(thisdict, synchronize_session=False)
    db.commit()

    # get the other members of the group and message them
    members = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.id == current_payee.group_id,
                                            models.LongTermGroupMember.approval_status == "approved",
                                            models.LongTermGroupMember.approval_count == 1).all()

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


# creating a withdrawal from long term group made by user in version code 7
@router.post("/user_long_term_group_withdrawal", status_code=status.HTTP_201_CREATED, response_model=schemas.TransactionOut)
def user_create_withdraw_from_long_term_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db),
                                    current_user: int = Depends(oauth2.get_current_user)):
    # check for the group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                  models.LongTermGroupMember.group_id == group_given.group_id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")

    # then check whether the user is eligible to withdraw money;  for the user to withdraw:
    # -the payout date must have matured
    # if all conditions are met, allow the user to withdraw, register the withdraw, update the group balance and message all group members about the withdrawal

    #let's check whether payout date has matured.
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    expiry_date_string = str(group_check.payout_date)
    expiry_date_object = datetime.strptime(expiry_date_string, format_string)
    now_string = str(datetime.now())
    now = datetime.strptime(now_string, format_string)
    # maturity_object = now-create_date
    # loan_maturity = maturity_object.days

    if now < expiry_date_object:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"withdrawal not allowed. Payout date not yet reached")

    if now > expiry_date_object:

        #let us first check whether the user has already withdrawn their share
        withdraw_check = db.query(models.LongTermGroupTransaction).filter(models.LongTermGroupTransaction.user_id == current_user.id,
                                                                          models.LongTermGroupTransaction.transaction_type == "withdraw",
                                                                          models.LongTermGroupTransaction.cycle == str(group_check.cycle)).all()


        if withdraw_check:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"withdrawal not allowed. you have already withdrawn your share")

        # let us get the total deposits(withdrawable amount) of the current user
        total_user_deposits = 0

        deposits = db.query(models.LongTermGroupTransaction).filter(models.LongTermGroupTransaction.user_id == current_user.id,
                                                                    models.LongTermGroupTransaction.transaction_type == "deposit",
                                                                    models.LongTermGroupTransaction.cycle == str(group_check.cycle)).all()

        for deposit in deposits:
            total_user_deposits += deposit.amount


        print(total_user_deposits)

        if total_user_deposits < 1500:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"money is too little to withdraw")

        sambax_charge = 0.05 * total_user_deposits
        withdrawable_amount = total_user_deposits - sambax_charge


        #add logic to perform the withdraw
        appendage = '256'
        number_string = str(current_user.phone_number)
        usable_phone_number_string = appendage + number_string
        usable_phone_number = int(usable_phone_number_string)

        old_group_balance = group_check.account_balance
        new_group_balance = old_group_balance - total_user_deposits

        # register withdraw
        new_withdraw = models.LongTermGroupTransaction(user_id=current_user.id, group_id=group_given.group_id,
                                                      amount=withdrawable_amount,
                                                      cycle=group_check.cycle, transaction_type="withdraw",
                                                      old_balance=old_group_balance, new_balance=new_group_balance)
        db.add(new_withdraw)
        db.commit()
        db.refresh(new_withdraw)

        # use a random dictionary to update the account balance
        thisdict = {

            "account_balance": 1964,

        }

        thisdict["account_balance"] = new_group_balance


        # update the account balance of the group
        group_account_query = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id)
        group_account_query.update(thisdict, synchronize_session=False)
        db.commit()

        # change the cycle of the group if  the account balance of the group is 0
        group_dance = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id).first()
        now_cycle = group_dance.cycle
        now_group_balance = group_dance.account_balance

        if now_group_balance == 0:
            new_cycle_now = now_cycle + 1


            cycle_week_dict = {
                "cycle": 1964,

            }


            cycle_week_dict["cycle"] = new_cycle_now


            group_kologa = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id)
            group_kologa.update(cycle_week_dict, synchronize_session=False)
            db.commit()

        # send message to all group members about group balance update
        # get the other members of the group and message them
        members = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.group_id == group_given.group_id,
                                                models.LongTermGroupMember.approval_status == "approved",
                                                models.LongTermGroupMember.approval_count == 1).all()

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
                    'message': f'Hello, {user.first_name},{current_user.first_name} has withdrawn UgX{total_user_deposits} from your group{group_given.group_id} savings at Sambax Finance Ltd.Your new group balance UgX{new_group_balance}.',
                    'reciever': f'{usable_phone_number2}'}
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            test_response = requests.post(url, data=data, headers=headers)
            if test_response.status_code == 200:
                print("message success")

    return new_withdraw


# getting all payments, made to a long term saving group in version code 7
@router.post("/long_term_group_general_statement", response_model=List[schemas.LongTermGroupPaymentsInquiryOut])
def get_all_payments_for_this_long_term_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db),
                                        current_user: int = Depends(oauth2.get_current_user)):
    list_details = []

    # check the group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                  models.LongTermGroupMember.group_id == group_given.group_id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")

    payments = db.query(models.LongTermGroupTransaction).filter(models.LongTermGroupTransaction.group_id == group_given.group_id,
                                                    models.LongTermGroupTransaction.cycle == str(group_check.cycle)
                                                    ).all()
    if not payments:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"there are no payments for this group in  this cycle")

    for payment in payments:
        user = db.query(models.User).filter(models.User.id == payment.user_id).first()

        # lets add a zero to the phone number
        appendage = '0'
        number_string = str(user.phone_number)
        usable_phone_number_string = appendage + number_string

        user_details2 = {"amount": payment.amount,
                         "old_balance": payment.old_balance,
                         "new_balance": payment.new_balance,
                         "transaction_type": payment.transaction_type,
                         "first_name": user.first_name,
                         "last_name": user.last_name,
                         "phone_number": usable_phone_number_string,
                         "created_at": payment.created_at}

        # payment_details.append(user_details)
        list_details.append(user_details2)

    return list_details


# Setting a new payout date for a long term group by user in version Code 7
@router.post("/set_new_payout_date_for_long_term_group", status_code=status.HTTP_201_CREATED, response_model=schemas.LongTermGroupOut)
def set_new_payout_date_for_long_term_group(group: schemas.UpdatePayout, db: Session = Depends(get_db),
                             current_user: int = Depends(oauth2.get_current_user)):
    # check the group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # first check whether user is an admin to this group
    user_group = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group.group_id,
                                                       models.LongTermGroup.group_admin == current_user.id).first()

    if not user_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"You are not admin to this saving group")

    # let's check whether payout date has matured. If payout date is matured, and the group account balance is zero, then allow admin to reset payout date
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    expiry_date_string = str(group_check.payout_date)
    expiry_date_object = datetime.strptime(expiry_date_string, format_string)
    now_string = str(datetime.now())
    now = datetime.strptime(now_string, format_string)
    # maturity_object = now-create_date
    # loan_maturity = maturity_object.days

    if now < expiry_date_object:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You can not change payout date now. Current Payout date has not yet expired")

    if group_check.account_balance > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You can only change the payout date if the group account balance is 0")

    if group_check.account_balance == 0:

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

        group_kologa = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group.group_id)
        group_kologa.update(thisdict, synchronize_session=False)
        db.commit()

    return group_check


# getting specific user statement, made to a long term saving group in version code 7
@router.post("/my_personal_statement_in_long_term_group", response_model=List[schemas.LongTermGroupPaymentsInquiryOut])
def my_total_deposits_in_long_term_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db),
                                        current_user: int = Depends(oauth2.get_current_user)):
    list_details = []

    # check the group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                  models.LongTermGroupMember.group_id == group_given.group_id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")

    payments = db.query(models.LongTermGroupTransaction).filter(models.LongTermGroupTransaction.group_id == group_given.group_id,
                                                                models.LongTermGroupTransaction.user_id == current_user.id,
                                                                models.LongTermGroupTransaction.cycle == str(group_check.cycle),
                                                                models.LongTermGroupTransaction.transaction_type == "deposit"

                                                    ).all()
    if not payments:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"there are no payments for this group in  this cycle")

    for payment in payments:
        user = db.query(models.User).filter(models.User.id == payment.user_id).first()

        # lets add a zero to the phone number
        appendage = '0'
        number_string = str(user.phone_number)
        usable_phone_number_string = appendage + number_string

        user_details2 = {"amount": payment.amount,
                         "old_balance": payment.old_balance,
                         "new_balance": payment.new_balance,
                         "transaction_type": payment.transaction_type,
                         "first_name": user.first_name,
                         "last_name": user.last_name,
                         "phone_number": usable_phone_number_string,
                         "created_at": payment.created_at}

        # payment_details.append(user_details)
        list_details.append(user_details2)

    return list_details


# getting total specific user deposits, made to a long term saving group in version code 7
@router.post("/my_total_deposits_in_long_term_group", response_model=schemas.GetMyTotalDeposits)
def my_total_deposits_in_long_term_group(group_given: schemas.NewGroupWithdraw, db: Session = Depends(get_db),
                                        current_user: int = Depends(oauth2.get_current_user)):


    # check the group
    group_check = db.query(models.LongTermGroup).filter(models.LongTermGroup.id == group_given.group_id).first()

    if not group_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"saving group does not exist")

    # check whether user belongs to this group
    current_payee = db.query(models.LongTermGroupMember).filter(models.LongTermGroupMember.user_id == current_user.id,
                                                  models.LongTermGroupMember.group_id == group_given.group_id,
                                                  models.LongTermGroupMember.approval_status == "approved",
                                                  models.LongTermGroupMember.approval_count == 1).first()

    if not current_payee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"user does not belong to this saving group")

    # let us get the total deposits(withdrawable amount) of the current user
    total_user_deposits = 0

    deposits = db.query(models.LongTermGroupTransaction).filter(
        models.LongTermGroupTransaction.user_id == current_user.id,
        models.LongTermGroupTransaction.transaction_type == "deposit",
        models.LongTermGroupTransaction.cycle == str(group_check.cycle)).all()

    for deposit in deposits:
        total_user_deposits += deposit.amount

    print(total_user_deposits)
    my_total_deposit_dict = {"total_deposits":total_user_deposits}


    return my_total_deposit_dict