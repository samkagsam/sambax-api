
#from database import Base
#import database
from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship





class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, nullable=False)
    loan_principle = Column(Integer, nullable=False)
    loan_interest_rate = Column(Integer, nullable=False)
    loan_interest = Column(Integer, nullable=False)
    loan_payable = Column(Integer, nullable=False)
    loan_balance = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    loan_period = Column(Integer, nullable=False)
    expiry_date = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    running = Column(Boolean, server_default="True", nullable=True)
    loan_type = Column(String, nullable=False, server_default='Business')





class Biodata(Base):
    __tablename__ = "biodata"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=True)
    home_address = Column(String, nullable=False)
    work_address = Column(String, nullable=False)
    customer_contact_one = Column(String, nullable=False)
    customer_contact_two = Column(String, nullable=True)
    guarantor_one = Column(String, nullable=False)
    guarantor_two = Column(String, nullable=True)
    guarantor_one_contact = Column(String, nullable=False)
    guarantor_two_contact = Column(String, nullable=True)
    guarantor_two_relationship = Column(String, nullable=True)
    guarantor_one_relationship = Column(String, nullable=False)
    customer_id_url = Column(String, nullable=True)
    customer_image_url = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    business_picture_url = Column(String, nullable=True)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    phone_number = Column(Integer, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    first_name = Column(String, nullable=False, server_default='None')
    last_name = Column(String, nullable=False, server_default='None')
    account_balance = Column(Integer, nullable=False, server_default='0')
    customer_image_url = Column(String, nullable=True)
    customer_id_url = Column(String, nullable=True)
    network = Column(String, nullable=False, server_default='other')
    group = Column(Integer, nullable=True)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=True)
    home_address = Column(String, nullable=False)
    work_address = Column(String, nullable=False)
    nature_of_business = Column(String, nullable=False)
    contact_one = Column(Integer, nullable=False)
    contact_two = Column(Integer, nullable=True)
    requested_loan_amount = Column(Integer, nullable=False)
    guarantor_one = Column(String, nullable=False)
    guarantor_two = Column(String, nullable=True)
    guarantor_one_contact = Column(Integer, nullable=False)
    guarantor_two_contact = Column(Integer, nullable=False)
    guarantor_two_relationship = Column(String, nullable=True)
    guarantor_one_relationship = Column(String, nullable=False)
    customer_id_url = Column(String, nullable=True)
    customer_image_url = Column(String, nullable=True)

    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose_for_loan = Column(String, nullable=False, server_default='None')


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    old_balance = Column(Integer, nullable=False, server_default='0')
    new_balance = Column(Integer, nullable=False, server_default='0')
    transaction_type = Column(String, nullable=False, server_default='None')
    made_by = Column(String, nullable=False, server_default='None')
    owner = relationship("Loan")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, nullable=False)
    phone_number = Column(Integer, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    old_balance = Column(Integer, nullable=False, server_default='0')
    new_balance = Column(Integer, nullable=False, server_default='0')
    made_by = Column(String, nullable=False, server_default='admin')


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, nullable=False)
    payout = Column(Integer, nullable=False, server_default='0')
    account_balance = Column(Integer, nullable=False, server_default='0')
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    group_admin = Column(Integer, nullable=False, server_default='0')
    cycle_balance = Column(Integer, nullable=False, server_default='0')
    cycle_change = Column(Integer, nullable=False, server_default='0')
    cycle = Column(Integer, nullable=False, server_default='0')
    week = Column(Integer, nullable=False, server_default='0')



class Payee(Base):
    __tablename__ = "payees"

    id = Column(Integer, primary_key=True, nullable=False)
    week = Column(Integer, nullable=False, server_default='0')
    group = Column(Integer, nullable=False, server_default='0')
    user_id = Column(Integer, nullable=False, server_default='0')
    cycle = Column(String, nullable=False, server_default='None')
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    approval_status = Column(String, nullable=False, server_default='None')
    approval_count = Column(Integer, nullable=False, server_default='0')


class GroupPayment(Base):
    __tablename__ = "group_payments"

    id = Column(Integer, primary_key=True, nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    week = Column(Integer, nullable=False, server_default='0')
    cycle = Column(String, nullable=False, server_default='None')
    transaction_type = Column(String, nullable=False, server_default='None')
