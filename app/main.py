from typing import Optional, List

from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Body
from pydantic import BaseModel

from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from . import models, schemas, utils
from .database import engine, get_db
from sqlalchemy.orm import Session
from .routers import user, biodata, loan, application, payment, auth, admin_auth, transaction
from .config import Settings




models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [

    "*"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(biodata.router)
app.include_router(loan.router)
app.include_router(application.router)
app.include_router(payment.router)
app.include_router(auth.router)
app.include_router(admin_auth.router)
app.include_router(transaction.router)



@app.get("/")
def root():
    return {"message": "hello.welcome to sambax api!!!!!!!!!"}





