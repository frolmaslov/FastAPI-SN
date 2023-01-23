from fastapi import APIRouter, Depends
from typing import List
from .. import schemas, database, models
from sqlalchemy.orm import Session


router = APIRouter()


@router.get('/blog', response_model=List[schemas.ShowBlog], tags=['blogs'])
async def all(db: Session=Depends(database.get_db)):
    blogs = db.query(models.Blog).all()
    return blogs