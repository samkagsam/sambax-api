from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2
from ..database import engine, get_db
from typing import Optional, List


router = APIRouter(
    tags=["Authentication"]
)


#login a user
@router.post("/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.phone_number == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")

    #create token
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    #return token

    return {"access_token": access_token, "token_type": "bearer"}
