from fastapi import FastAPI, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from starlette import status


app = FastAPI()


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id: int, title: str, author: str, description: str, rating: int, published_date: int):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    id: Optional[int] = Field(
        description="id is not needed on create", default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, le=5)
    published_date: int = Field(gt=1999)

    @field_validator("published_date")
    def validate_published_date(cls, value):
        # cls: used in Pydantic, refers to the class itself
        # value: the value of the validated attribute from request body
        # now we can validate date dynamically.
        current_year = date.today().year
        if value > current_year:
            raise ValueError("published date cannot be in the future")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "new book title",
                "author": "Mingfang",
                "description": "nice book",
                "rating": 5,
                "published_date": 2012
            }
        }
    }


BOOKS = [
    Book(1, "title one", "author one", "nice book", 4, 2012),
    Book(2, "title two", "author two", "great book", 5, 2015),
    Book(3, "title three", "author one", "good book", 3, 2017)
]


@app.get("/books", status_code=status.HTTP_200_OK)
async def read_all_book():
    return BOOKS


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def read_book_by_id(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail=f"book {book_id} cannot be found")


'''
def validate_query(
    rating: Optional[int] = Query(None, gt=0, le=5), # match the query parameter in the request url
    published_date: Optional[int] = Query(None, gt=1999)
):
    current_year = date.today().year
    if published_date and published_date > current_year:
        raise HTTPException(
            status_code=400, detail="Published date cannot be in the future")
        # in validator, we use ValueError. for dependencies function, we use HTTPException
    return {"rating": rating, "published_date": published_date} 
# if validation passes, we return the validated data. this becomes the value for Depends(validate_query) and will be used as validated_data in the router function

# Fastapi calls validate_query while passing in the query parameters first when a request has been made. then get the validated data in a dictionary called validated_data and use it in the router function
@app.get("/books/")
async def read_book_by_rating_and_date(validated_data: dict = Depends(validate_query)):
    booklist = BOOKS
    if validated_data.get("rating") is not None:
        booklist = [book for book in booklist if book.rating == validated_data.get("rating")]
    if validated_data.get("published_date") is not None:
        booklist = [book for book in booklist if book.published_date == validated_data.get("published_date")]
'''

class BookQuery(BaseModel):
    rating: Optional[int] = Query(None, gt=0, le=5, description="Rating from 1 to 5")
    published_date: Optional[int] = Query(None, gt=1999)

    @field_validator("published_date")
    def validate_query_by_date(cls, value):
        current_year = date.today().year
        if value and value > current_year:  # value of pulished_date is int/None
            raise ValueError("Published date cannot be in the future")
        return value
    # returned value of "published_date" can be int or None


@app.get("/books/", status_code=status.HTTP_200_OK)
async def read_book_by_rating_and_date(bookquery: BookQuery = Depends()):
    booklist = BOOKS
    if bookquery.rating is not None:
        booklist = [
            book for book in booklist if book.rating == bookquery.rating]
    if bookquery.published_date is not None:
        booklist = [
            book for book in booklist if book.published_date == bookquery.published_date]
    return booklist

# @app.get("/books/")
# async def read_book_by_rating(
#     rating:Optional[int]=Query(None,gt=0,le=5,description="Rating from 1 to 5"),
#     # Query(default_value, validators, description)
# ):
#     booklist = [book for book in BOOKS if book.rating==rating]
#     return booklist


@app.post("/create-books", status_code=status.HTTP_201_CREATED)
async def create_book(book_request: BookRequest):
    new_book = Book(**book_request.model_dump())
    # convert the pydantics request into JSON, then use ** operator to assgin key-value pair into constructor
    BOOKS.append(assign_book_id(new_book))


def assign_book_id(book: Book):
    book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
    return book


@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(update_request: BookRequest):
    book_change = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == update_request.id:
            updated_book = Book(**update_request.model_dump())
            BOOKS[i] = updated_book
            book_change = True
    if not book_change:
        raise HTTPException(status_code=404, detail=f"{ \
                        update_request.id} is not found")


class PatchRequest(BaseModel):
    id: int
    title: Optional[str] = Field(min_length=3, default=None)
    author: Optional[str] = Field(min_length=1, default=None)
    description: Optional[str] = Field(
        min_length=1, max_length=100, default=None)
    rating: Optional[int] = Field(gt=0, le=5, default=None)
    published_date: Optional[int] = Field(gt=1999)

    @field_validator("published_date")
    def validate_published_date(cls, value):
        current_year = date.today().year
        if value > current_year:
            raise ValueError("Published date cannot be in the future")
        return value


@app.patch("/books/patch_book", status_code=status.HTTP_200_OK)
async def patch_book(patch_request: PatchRequest):
    for book in BOOKS:
        if book.id == patch_request.id:
            patch_info: dict = patch_request.model_dump(exclude_unset=True)
            # obtain a json dictionary with only the key-value pairs that are set in the request body. the ones whose values maintain as default are excluded
            for key, value in patch_info.items():
                if key != "id":  # skip handling id
                    # assign value to an attribute for python object (also able to dynamically create a new attribute) (assigns value to an attribute, not a dictionary key)
                    setattr(book, key, value)
                    # book[key] = value will not work because book here is only a class, not a dictionary. this assign a value to a dictionary key
            return book

            '''
            book.title = patch_request.title if patch_request.title is not None else book.title
            book.author = patch_request.author if patch_request.author is not None else book.author
            book.description = patch_request.description if patch_request.description is not None else book.description
            book.rating = patch_request.rating if patch_request.rating is not None else book.rating
            return book
            '''

    raise HTTPException(status_code=404, detail=f"{ \
                        patch_request.id} not found")


@app.delete("/books/{book_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int = Path(gt=0)):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_changed = True
            return
    raise HTTPException(status_code=404, detail=f"{book_id} not found")
