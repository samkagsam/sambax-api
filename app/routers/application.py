from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2
from ..database import engine, get_db
from typing import Optional, List


router = APIRouter(
    tags=["Applications"]
)


#getting all applications, used by admin
@router.get("/applications", response_model=List[schemas.ApplicationOut])
def get_applications(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    applications = db.query(models.Application).all()
    return applications


#getting all applications, made by a logged-in user
@router.get("/myapplications", response_model=List[schemas.ApplicationOut])
def get_my_applications(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    applications = db.query(models.Application).filter(models.Application.user_id == current_user.id).all()
    return applications


#creating an application
@router.post("/applications", status_code=status.HTTP_201_CREATED, response_model=schemas.ApplicationOut)
def create_application(application:schemas.Application, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    new_application = models.Application(user_id=current_user.id, **application.dict())
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    return new_application


#get one application
@router.get("/applications/{id}")
def get_application(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    application = db.query(models.Application).filter(models.Application.id == id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"application with id{id} was not found")

    return application


#deleting a single application
@router.delete("/applications/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    application = db.query(models.Application).filter(models.Application.id == id)
    if application.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"application with id{id} does not exist")

    application.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#updating a single application
@router.put("/applications/{id}", response_model=schemas.ApplicationOut)
def update_application(id: int, application: schemas.Application, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    application_query = db.query(models.Application).filter(models.Application.id == id)
    application_item = application_query.first()
    if application_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"application with id{id} does not exist")

    application_query.update(application.dict(), synchronize_session=False)
    db.commit()
    return application_query.first()

