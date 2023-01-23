import uvicorn
from fastapi import FastAPI, Depends, status, Response, HTTPException, Request, Security, Form
import models
import schemas
import database
from hashing import Hash
from sqlalchemy.orm import Session
from typing import List
import token_jwt
from datetime import timedelta
import oath2
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates




app = FastAPI()

models.database.Base.metadata.create_all(bind=database.engine)


templates = Jinja2Templates(directory="templates")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()





@app.get('/', response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
    

@app.get('/create', response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})



@app.post('/create', status_code=status.HTTP_201_CREATED, tags=['blogs'])
async def create(request: Request, title: str = Form(...),
    body: str = Form(...), db: Session=Depends(get_db)):
    
    new_blog = models.Blog(title=title, body=body)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
   
    return templates.TemplateResponse("success.html", {"request": request})


@app.put('/blog/{id}', status_code=status.HTTP_202_ACCEPTED, tags=['blogs'])
#async def update(id, request: schemas.Blog, db: Session=Depends(get_db), current_user: schemas.User = Depends(oath2.get_current_user)):
async def update(id, request: schemas.Blog, db: Session=Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id==id)
    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Blog with id {id} is not exist')
    else:
        blog.update({'body':request.body, 'id':id, 'title':request.title})
    db.commit()
    return 'updated'


@app.delete('/blog/{id}', status_code=status.HTTP_204_NO_CONTENT, tags=['blogs'])
async def delete_blog(id, db: Session=Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id==id)
    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Blog with id {id} is not exist')
    
    blog.delete(synchronize_session=False)
    db.commit()
    return 'done'

@app.get('/blog', response_class=HTMLResponse, response_model=List[schemas.ShowBlog], tags=['blogs'])
async def all(request: Request, db: Session=Depends(get_db)):
    blogs = db.query(models.Blog).all()
    return templates.TemplateResponse("blogs.html", {'request':request, 'blogs':blogs})

@app.get('/blog/{id}', status_code=200, response_class=HTMLResponse, response_model=schemas.ShowBlog, tags=['blogs'])
async def blog_id(id, response: Response, request: Request, db: Session=Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id==id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
         detail=f'Blog with id {id} is not available!')
        
    return templates.TemplateResponse("blog_id.html", {'request':request, 'blog':blog})




@app.post('/user', response_model=schemas.ShowUser, tags=['users'])
async def create_user(request: schemas.User, db: Session=Depends(get_db)):
    new_user = models.User(name=request.name, email=request.email, password=Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get('/user/{id}', response_model=schemas.ShowUser, tags=['users'])
async def get_user(id: str, db: Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.id==id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
         detail=f'User with id {id} is not found!')
    return user


@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/success")
def login(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.post('/login', tags=['authentication'])
async def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email==request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
         detail=f'Invalid name')
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
         detail=f'Incorrect password')
   
    access_token = token_jwt.create_access_token(data={"sub": user.email})
    
    return templates.TemplateResponse("success.html", {"request": {"access_token": access_token, "token_type": "bearer"}})
    



if __name__ == '__main__':
    uvicorn.run("main:app")