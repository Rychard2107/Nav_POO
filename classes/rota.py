# rota.py - Modelo de Rota com SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class Rota(Base):
    """Modelo de rota dentro de uma URL"""
    __tablename__ = "rotas"
    
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    caminho = Column(String(255), default="/", nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com URL e Conteúdo
    url = relationship("Url", back_populates="rotas")
    conteudo = relationship("Conteudo", back_populates="rota", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'Rota(id={self.id}, caminho="{self.caminho}", url_id={self.url_id})'
    
    def __str__(self):
        return f"Rota: {self.caminho}"
