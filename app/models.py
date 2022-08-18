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
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    loan_period = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    running = Column(Boolean, server_default="False", nullable=True)





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
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    phone_number = Column(Integer, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    first_name = Column(String, nullable=False, server_default='None')
    last_name = Column(String, nullable=False, server_default='None')


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
    business_picture_url = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("Loan")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, nullable=False)
    phone_number = Column(Integer, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
