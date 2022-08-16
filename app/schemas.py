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


class BiodataCreate(BiodataBase):
    pass


#determines the type of information received about a loan
class LoanBase(BaseModel):
    loan_holder: str
    loan_principle: int
    loan_interest_rate: int
    loan_period: str
    loan_interest: int
    loan_payable: int


class LoanCreate(LoanBase):
    pass


#determines the format of information sent back to a user after registration
class UserOut(BaseModel):
    id: int
    phone_number: int
    created_at: datetime

    class Config:
        orm_mode = True


#determines the type of information sent back about a customer
class Biodata(BiodataBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


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


#determines the type of information received to create a user
class UserCreate(BaseModel):
    phone_number: int
    password: str
    first_name: str
    last_name: str




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
    guarantor_two: str
    guarantor_one_contact: int
    guarantor_two_contact: int
    guarantor_two_relationship: str
    guarantor_one_relationship: str
    customer_id_url: str
    customer_image_url: str
    business_picture_url: str



#determines the format of application sent back to a user after registration
class ApplicationOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


#determines the format of payment information received from a user
class Payment(BaseModel):

    amount: int


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



