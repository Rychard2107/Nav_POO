# config.py - Configuração do banco de dados SQLite com SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Caminho do banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{BASE_DIR}/navigator.db"

# Criar engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Criar session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

def get_db():
    """Retorna uma sessão do banco de dados"""
    return SessionLocal()

def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    Base.metadata.create_all(bind=engine)
