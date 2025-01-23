from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


BOOKS = [{"title": "Title One", "author": "Author One", "category": "science"},
         {"title": "Title Two", "author": "Author Two", "category": "science"},
         {"title": "Title Three", "author": "Author Three", "category": "history"},
         {"title": "Title Four", "author": "Author Four", "category": "math"},
         {"title": "Title Five", "author": "Author Five", "category": "math"},
         {"title": "Title Six", "author": "Author Two", "category": "math"}]


@app.get("/books")
async def read_all_books():
    return BOOKS


@app.get("/books/{book_title}")
async def read_book(book_title: str):
    for book in BOOKS:
        if book.get("title").casefold() == book_title.casefold():
            return book


@app.get("/books/")
async def read_category_by_query(category: str):
    booklist = []
    for book in BOOKS:
        if book.get("category").casefold() == category.casefold():
            booklist.append(book)
    return booklist


@app.get("/books/author/")
async def read_books_of_author(author: str):
    booklist = []
    for book in BOOKS:
        if book.get("author").casefold() == author.casefold():
            booklist.append(book)
    return booklist


@app.get("/books/{author_name}/")
async def find_book(author_name: str, category: str):
    booklist = []
    for book in BOOKS:
        if book.get("author").casefold() == author_name.casefold() \
                and book.get("category").casefold() == category.casefold():
            booklist.append(book)

    return booklist


@app.get("/author/{author_name}")
async def read_books_of_author(author_name: str):
    booklist = []
    for book in BOOKS:
        if book.get("author").casefold() == author_name.casefold():
            booklist.append(book)
    return booklist


@app.post("/books/create_book")
async def create_book(new_book=Body()):
    BOOKS.append(new_book)


@app.put("/books/update_book")
async def update_book(updated_book=Body()):  # updated_book is a JSON dictionary
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold() == updated_book.get("title").casefold():
            BOOKS[i] = updated_book
            return BOOKS[i]


@app.patch("/books/{book_title}")
async def patch_book(book_title: str, patched_book: dict = Body()):
    for book in BOOKS:
        if book.get("title").casefold() == book_title.casefold():
            book["title"] = patched_book.get("title") or book["title"]
            book["author"] = patched_book.get("author") or book["author"]
            if patched_book.get("category") is not None:
                book["category"] = patched_book["category"]
            return book


class BookPatch(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None


@app.patch("/books/{book_title}")
async def patch_book(book_title: str, patched_book: BookPatch = Body()):
    for book in BOOKS:
        if book.get("title").casefold() == book_title.casefold():
            book["title"] = patched_book.title or book["title"]
            book["author"] = patched_book.author or book["author"]
            book["category"] = patched_book.category or book["category"]
            return book

    raise HTTPException(status_code=404, detail=f"{book_title} not found")


class BookUpdate(BaseModel):
    title: str
    author: str
    category: str


@app.put("/books/{book_title}")
async def update_book(book_title: str, updated_book: BookUpdate = Body()):
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold() == book_title.casefold():
            # turn the class updated_book into a dictionary
            BOOKS[i] = updated_book.model_dump()
            return BOOKS[i]

    raise HTTPException(status_code=404, detail=f"{book_title} not found")


@app.delete("/books/delete_book/{book_title}")
async def delete_book(book_title: str):
    for i in range(len(BOOKS)):
        if BOOKS[i].get("title").casefold() == book_title.casefold():
            BOOKS.pop(i)
            break
