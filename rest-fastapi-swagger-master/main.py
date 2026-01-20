from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import DBTerm, init_db, get_db
import uvicorn

init_db()

app = FastAPI(
    title="Glossary API (Терминологический глоссарий)",
    description="API для управления терминами ВКР, выполненное на FastAPI.",
    version="1.0.0"
)

class TermBase(BaseModel):
    definition: str

class TermCreate(TermBase):
    term: str

class Term(TermCreate):
    class Config:
        orm_mode = True

@app.get("/", summary="Главный маршрут")
def read_root():
    return {
        "message": "Welcome to the Glossary API (Терминологический глоссарий)"
    }

@app.get("/terms/", response_model=list[Term], summary="Получить список всех терминов")
def read_terms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    terms = db.query(DBTerm).offset(skip).limit(limit).all()
    return terms

@app.get("/terms/{term_key}", response_model=Term, summary="Получить информацию о конкретном термине")
def read_term(term_key: str, db: Session = Depends(get_db)):
    term = db.query(DBTerm).filter(DBTerm.term == term_key).first()
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    return term

@app.post("/terms/", response_model=Term, status_code=201, summary="Добавить новый термин")
def create_term(term: TermCreate, db: Session = Depends(get_db)):
    db_term = db.query(DBTerm).filter(DBTerm.term == term.term).first()
    if db_term:
        raise HTTPException(status_code=400, detail="Term already exists")

    new_term = DBTerm(term=term.term, definition=term.definition)
    db.add(new_term)
    db.commit()
    db.refresh(new_term)
    return new_term

@app.put("/terms/{term_key}", response_model=Term, summary="Обновить существующий термин")
def update_term(term_key: str, updated_term: TermBase, db: Session = Depends(get_db)):
    db_term = db.query(DBTerm).filter(DBTerm.term == term_key).first()
    if db_term is None:
        raise HTTPException(status_code=404, detail="Term not found")

    db_term.definition = updated_term.definition
    db.commit()
    db.refresh(db_term)
    return db_term

@app.delete("/terms/{term_key}", summary="Удалить термин")
def delete_term(term_key: str, db: Session = Depends(get_db)):
    db_term = db.query(DBTerm).filter(DBTerm.term == term_key).first()
    if db_term is None:
        raise HTTPException(status_code=404, detail="Term not found")

    db.delete(db_term)
    db.commit()
    return {"message": f"Term '{term_key}' deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
