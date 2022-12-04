from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2, admin_oauth2
from ..database import engine, get_db
from typing import Optional, List


router = APIRouter(
    tags=["Applications"]
)




#getting all applications, made by a logged-in user
@router.get("/myapplications", response_model=List[schemas.ApplicationOut])
def get_my_applications(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    applications = db.query(models.Application).filter(models.Application.user_id == current_user.id).all()
    return applications


#creating an application
@router.post("/applications", status_code=status.HTTP_201_CREATED, response_model=schemas.ApplicationOut)
def create_application(application:schemas.Application, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #check whether user has a running loan
    current_loan = db.query(models.Loan).filter(models.Loan.user_id == current_user.id, models.Loan.running == True).first()

    if current_loan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"you already have a running loan. you can't apply")
    thisdict = application.dict()
    thisdict["first_name"] = current_user.first_name
    thisdict["last_name"] = current_user.last_name
    thisdict["contact_one"] = current_user.phone_number

    #new_application = models.Application(user_id=current_user.id, **application.dict())
    new_application = models.Application(user_id=current_user.id, **thisdict)
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    return new_application


#getting all applications, used by admin
@router.get("/admin/applications", response_model=List[schemas.AdminApplicationOut])
def get_applications(db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    applications = db.query(models.Application).all()
    return applications


#get one application by admin
@router.get("/admin/applications/{id}")
def get_application(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):
    application = db.query(models.Application).filter(models.Application.id == id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"application with id{id} was not found")

    return application


#deleting a single application by admin
@router.delete("/admin/applications/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(id: int, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    application = db.query(models.Application).filter(models.Application.id == id)
    if application.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"application with id{id} does not exist")

    application.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#updating a single application by admin
@router.put("/admin/applications/{id}", response_model=schemas.ApplicationOut)
def update_application(id: int, application: schemas.Application, db: Session = Depends(get_db), current_admin: int = Depends(admin_oauth2.get_current_admin)):

    application_query = db.query(models.Application).filter(models.Application.id == id)
    application_item = application_query.first()
    if application_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"application with id{id} does not exist")

    application_query.update(application.dict(), synchronize_session=False)
    db.commit()
    return application_query.first()

