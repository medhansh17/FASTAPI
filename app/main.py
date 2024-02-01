from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends
from fastapi.params import Body
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from sqlalchemy.orm import Session
from . import models, schemas
from .databse import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


while True:
    try:
        conn = psycopg2.connect(
            host='localhost', database='fastapi', user='postgres', password='mydata', cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Datbase connection was successfull")
        break
    except Exception as erorr:
        print("Connection to database failed")
        print("Erorr", erorr)
        time.sleep(2)


my_posts = [{"title": "Title of post 1",
             "content": "Content of  post 1", "id": 1}]


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/posts", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    # cursor.execute("""SELECT * FROM posts """)
    # posts = cursor.fetchall()
    posts = db.query(models.Post).all()
    return posts


@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.Postcreate, db: Session = Depends(get_db)):
    # cursor.execute("""INSERT INTO posts (title,content,published) VALUES (%s,%s,%s) RETURNING *""",
    #                (post.title, post.content, post.published))  # avoid SQL injection
    # new_post = cursor.fetchone()
    # conn.commit()
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/posts/{id}", response_model=schemas.Post)
def get_posts(id: int, db: Session = Depends(get_db)):
    # cursor.execute("""SELECT * FROM posts WHERE id = %s""",
    #                (id,))  # comma after id to create tuple
    # post = cursor.fetchone()
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {id} was not found.")
    return post


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    # cursor.execute("""DELETE FROM posts WHERE id = %s""", (id,))
    # conn.commit()
    post = db.query(models.Post).filter(models.Post.id == id)
    if post.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {id} was not found.")
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}")
def update_post(id: int, post: schemas.Postcreate, db: Session = Depends(get_db)):
    # cursor.execute(
    #     """UPDATE posts  SET title = %s , content = %s , published = %s WHERE id = %s RETURNING *""", (post.title, post.content, post.published, id,))
    # updated_post = cursor.fetchone()
    # conn.commit()
    existing_post = db.query(models.Post).filter(models.Post.id == id).first()
    print(existing_post)
    if existing_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The post with the id {id} was not found")

    # Update the post
    existing_post.title = post.title
    existing_post.content = post.content
    existing_post.published = post.published

    db.commit()

    return existing_post.model_dump()
