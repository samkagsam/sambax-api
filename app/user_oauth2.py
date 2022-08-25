from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from .schemas import TokenData
from sqlalchemy.orm import Session
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user_signup")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"could not validate credentials",
                                           headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        otp: int = payload.get("otp")
        first_name: str = payload.get("first_name")
        last_name: str = payload.get("last_name")
        phone_number: int = payload.get("phone_number")
        password: str = payload.get("password")


        if otp is None:
            raise credentials_exception
        token_data = schemas.SignTokenData(otp=otp, first_name=first_name, last_name=last_name,
                                           phone_number=phone_number, password=password)
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_registration_attempt(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"could not validate credentials",
                                           headers={"WWW-Authenticate":"Bearer"})
    token = verify_access_token(token, credentials_exception)
    #user = db.query(models.User).filter(models.User.id == token.id).first()



    return token



