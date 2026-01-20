import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db, DBTerm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_module(module):
    """Настройка перед тестами"""
    # Создаем таблицы
    DBTerm.metadata.create_all(bind=engine)

def teardown_module(module):
    """Очистка после тестов"""
    DBTerm.metadata.drop_all(bind=engine)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_create_term():
    term_data = {
        "term": "Тестовый термин",
        "definition": "Это тестовое определение"
    }
    response = client.post("/terms/", json=term_data)
    assert response.status_code == 201
    data = response.json()
    assert data["term"] == term_data["term"]
    assert data["definition"] == term_data["definition"]

def test_get_terms():
    response = client.get("/terms/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_specific_term():
    response = client.get("/terms/Тестовый термин")
    assert response.status_code == 200
    data = response.json()
    assert data["term"] == "Тестовый термин"

def test_update_term():
    update_data = {"definition": "Обновленное определение"}
    response = client.put("/terms/Тестовый термин", json=update_data)
    assert response.status_code == 200
    assert response.json()["definition"] == "Обновленное определение"

def test_delete_term():
    response = client.delete("/terms/Тестовый термин")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

def test_term_not_found():
    response = client.get("/terms/НесуществующийТермин")
    assert response.status_code == 404

def test_create_existing_term():
    term_data = {
        "term": "Дубликат",
        "definition": "Первое определение"
    }
    client.post("/terms/", json=term_data)
    
    # Попытка создать дубликат
    response = client.post("/terms/", json=term_data)
    assert response.status_code == 400