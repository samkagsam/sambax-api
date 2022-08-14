from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils
from ..database import engine, get_db
from typing import Optional, List


router = APIRouter(
    tags=["Biodata"]
)


#get all biodata
@router.get("/biodata", response_model=List[schemas.Biodata])
def get_all_biodata(db: Session = Depends(get_db)):

    biodata = db.query(models.Biodata).all()
    return biodata


#create biodata
@router.post("/biodata", status_code=status.HTTP_201_CREATED, response_model=schemas.Biodata)
def create_biodata(biodata: schemas.BiodataCreate, db: Session = Depends(get_db)):

    new_biodata = models.Biodata(**biodata.dict())
    db.add(new_biodata)
    db.commit()
    db.refresh(new_biodata)

    return new_biodata


#getting a single biodata profile
@router.get("/biodata/{id}", response_model=schemas.Biodata)
def get_biodata(id: int, db: Session = Depends(get_db)):

    biodata = db.query(models.Biodata).filter(models.Biodata.id == id).first()
    if not biodata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"biodata for id{id} was not found")

    return biodata


#updating biodata
@router.put("/biodata/{id}", response_model=schemas.Biodata)
def update_biodata(id: int, biodata:schemas.BiodataCreate, db: Session = Depends(get_db)):
    biodata_query = db.query(models.Biodata).filter(models.Biodata.id == id)
    biodata_item = biodata_query.first()

    if biodata_item == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"biodata for id{id} does not exist")

    biodata_query.update(biodata.dict(), synchronize_session=False)
    db.commit()
    return  biodata_query.first()


#deleting a single biodata
@router.delete("/biodata/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_biodata(id: int, db: Session = Depends(get_db)):

    biodata = db.query(models.Biodata).filter(models.Biodata.id == id)
    if biodata.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"biodata for id{id} does not exist")

    biodata.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


