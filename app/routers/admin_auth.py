from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2, admin_utils
from ..database import engine, get_db
from typing import Optional, List


router = APIRouter(
    tags=[" Admin Authentication"]
)


#login admin
@router.post("/admin_login", response_model=schemas.Token)
def admin_login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    admin = db.query(models.Admin).filter(models.Admin.phone_number == user_credentials.username).first()

    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if not admin_utils.verify(user_credentials.password, admin.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")

    #create token
    admin_access_token = admin_oauth2.create_access_token(data={"admin_id": admin.id})
    #return token

    return {"access_token": admin_access_token, "token_type": "bearer"}
