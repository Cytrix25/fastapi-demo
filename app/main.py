from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column()

class NoteIn(BaseModel):
    text: str

class NoteOut(BaseModel):
    id: int
    text: str
    class Config:
        from_attributes = True  # Pydantic v2

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello, Lieutenant Hansen"}

@app.get("/dbtime")
def db_time():
    with engine.connect() as conn:
        now = conn.execute(text("SELECT NOW()")).scalar()
    return {"database_time": now.isoformat()}

@app.post("/notes", response_model=NoteOut)
def create_note(note: NoteIn, db: Session = Depends(get_db)):
    obj = Note(text=note.text)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/notes", response_model=list[NoteOut])
def list_notes(db: Session = Depends(get_db)):
    return db.execute(select(Note)).scalars().all()

@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    obj = db.get(Note, note_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj

@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note: NoteIn, db: Session = Depends(get_db)):
    obj = db.get(Note, note_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    obj.text = note.text
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    obj = db.get(Note, note_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(obj)
    db.commit()
    return {"deleted": note_id}
