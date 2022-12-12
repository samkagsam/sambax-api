from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from pydantic.types import conint


#determines the type of information received about a customer
class BiodataBase(BaseModel):
    first_name: str
    middle_name: str
    last_name: str
    gender: str
    date_of_birth: str
    home_address: str
    work_address: str
    customer_contact_one: str
    customer_contact_two: str
    guarantor_one: str
    guarantor_two: str
    guarantor_one_contact: str
    guarantor_two_contact: str
    guarantor_two_relationship: str
    guarantor_one_relationship: str
    customer_id_url: str
    customer_image_url: str
    business_picture_url: str


class BiodataCreate(BiodataBase):
    pass


#determines the type of information sent back about a customer
class Biodata(BiodataBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


#determines the type of information received about a loan
class LoanBase(BaseModel):
    loan_principle: int
    loan_interest_rate: int
    loan_interest: int
    loan_payable: int
    loan_balance: int
    loan_period: int
    user_id: int
    loan_type: str




class LoanCreate(LoanBase):
    pass


#determines the type of information sent back about a loan
class Loan(LoanBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


#determines the type of information sent back on loan balance request
class LoanBalance(BaseModel):
    loan_balance: str
    expiry_date: str

    class Config:
        orm_mode = True


#determines the type of information received from an admin about loan maturity, it's the number of days
class LoanMaturity(BaseModel):
    sought_maturity: int



#determines the type of information received to create a user
class UserCreate(BaseModel):
    phone_number: int
    password: str
    first_name: str
    last_name: str
    customer_image_url: str
    customer_id_url: str


#determines the format of information sent back to a user after registration
class UserOut(BaseModel):
    id: int
    phone_number: int
    created_at: datetime

    class Config:
        orm_mode = True



#determines the format of information received from a user at registration
class Application(BaseModel):

    first_name: str
    middle_name: str
    last_name: str
    gender: str
    date_of_birth: str
    home_address: str
    work_address: str
    nature_of_business: str
    contact_one: int
    contact_two: int
    requested_loan_amount: int
    guarantor_one: str
    guarantor_one_contact: int
    guarantor_one_relationship: str
    guarantor_two: str
    guarantor_two_contact: int
    guarantor_two_relationship: str
    customer_id_url: str
    customer_image_url: str
    purpose_for_loan: str



#determines the format of application sent back to a user after registration
class ApplicationOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


#determines the format of application sent back to admin on inquiry
class AdminApplicationOut(BaseModel):
    id: int
    first_name: str
    middle_name: str
    last_name: str
    gender: str
    date_of_birth: str
    home_address: str
    work_address: str
    nature_of_business: str
    contact_one: int
    contact_two: int
    requested_loan_amount: int
    guarantor_one: str
    guarantor_one_contact: int
    guarantor_one_relationship: str
    guarantor_two: str
    guarantor_two_contact: int
    guarantor_two_relationship: str
    customer_id_url: str
    customer_image_url: str
    purpose_for_loan: str

    class Config:
        orm_mode = True


#determines the format of payment information received from a user
class Payment(BaseModel):

    amount: int


#determines the format of payment information entered by admin about a user
class AdminPayment(BaseModel):

    amount: int
    phone_number: int


#determines the format of information sent back to a user after making payment
class PaymentCreate(BaseModel):
    id: int
    amount: int
    created_at: datetime
    owner: LoanBalance

    class Config:
        orm_mode = True

#determines the format of information sent back to a user about payment
class PaymentOut(BaseModel):
    id: int
    amount: int
    created_at: datetime


    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    phone_number: int
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class SignTokenData(BaseModel):
    otp: Optional[int] = None
    phone_number: int
    password: str
    first_name: str
    last_name: str
    customer_image_url: str
    customer_id_url: str


class TokenOtp(BaseModel):
    otp: int


class ReceivedDates(BaseModel):
    from_date: str
    to_date: str


#determines the format of application sent back to a user after registration
class LandingPage(BaseModel):
    first_name: str
    account_balance: str
    loan_balance: str

    class Config:
        orm_mode = True


#determines the format of transaction information received from a user
class TransactionIn(BaseModel):

    amount: int


#determines the format of information sent back to a user about a transaction
class TransactionOut(BaseModel):
    id: int
    amount: int
    transaction_type: str
    created_at: datetime


    class Config:
        orm_mode = True


class PhoneNumberRecover(BaseModel):
    phone_number: int


class RecoverTokenData(BaseModel):
    otp: Optional[int] = None
    phone_number: int


class PasswordChange(BaseModel):
    password:str


#determines the type of information received about a group
class GroupCreate(BaseModel):
    payout: int


#determines the format of application sent back to admin after group registration
class GroupOut(BaseModel):
    id: int
    payout: int
    created_at: datetime

    class Config:
        orm_mode = True


#determines the type of information received about a payee
class PayeeCreate(BaseModel):
    phone_number: int
    group_id: int
    week_no: int
    cycle: str


#determines the type of information received about a payee from a user admin
class UserPayeeCreate(BaseModel):
    phone_number: int




#determines the format of application sent back to admin after payee registration
class PayeeOut(BaseModel):
    id: int
    week: int
    group: int
    cycle: str
    created_at: datetime

    class Config:
        orm_mode = True


#determines the format of payment information entered by admin about a user
class AdminGroupPaymentIn(BaseModel):

    amount: int
    phone_number: int
    week: int
    cycle: str


#determines the format of payment information for group entered by a user
class GroupPaymentIn(BaseModel):
    amount: int
    week: int
    cycle: str


#determines the format of payment information for group entered by a user in version code 6
class NewGroupPaymentIn(BaseModel):
    amount: int
    group_id: int


#determines the format of payment information for group inquired by a user
class GroupPaymentsInquiry(BaseModel):
    cycle: str
    week: int


#determines the format of information sent sent back to a user about group payments
class GroupPaymentsInquiryOut(BaseModel):

    first_name: str
    last_name: str
    phone_number: str
    amount: str
    created_at: datetime

    class Config:
        orm_mode = True


#determines the format of information sent sent by a user to make a withdraw
class GroupWithdraw(BaseModel):
    week: int
    cycle: str

#determines the format of information sent sent by a user to make a withdraw in version code 6
class NewGroupWithdraw(BaseModel):
    group_id: int




#determines the format of information sent back to a user about a group
class GroupLandingPage(BaseModel):
    usergroup: str
    group_payout: str
    group_account_balance: str

    class Config:
        orm_mode = True


#determines the format of application sent back to admin after payee registration
class GroupMembers(BaseModel):

    first_name: str
    last_name: str
    phone_number: str


    class Config:
        orm_mode = True


#determines the format of data sent about group members in Version Code 6
class AllGroupMembers(BaseModel):

    first_name: str
    last_name: str
    phone_number: str
    user_week: str


    class Config:
        orm_mode = True



#determines the format of information sent back to user on seeking group requests
class GroupRequestOut(BaseModel):
    request_id:str
    group_number: str
    admin_first_name: str
    admin_last_name: str
    admin_phone_number:str

    class Config:
        orm_mode = True


#determines the format of information sent  to api on approving request
class ApprovalRequestIn(BaseModel):
    id:int



#determines the format of information sent back to user on approving request
class ApprovalRequestOut(BaseModel):
    id:int
    group: int
    approval_status: str
    approval_count: int


    class Config:
        orm_mode = True


class UserGroupsOut(BaseModel):
    id: int
    class Config:
        orm_mode = True
