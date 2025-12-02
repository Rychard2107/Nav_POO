# conteudo.py - Modelo de Conteúdo com SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class Conteudo(Base):
    """Modelo de conteúdo armazenado no banco de dados"""
    __tablename__ = "conteudos"
    
    id = Column(Integer, primary_key=True, index=True)
    rota_id = Column(Integer, ForeignKey("rotas.id"), nullable=False)
    titulo = Column(String(255), default="")
    texto = Column(Text, default="")
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Rota
    rota = relationship("Rota", back_populates="conteudo")
    
    def __repr__(self):
        return f'Conteúdo(id={self.id}, titulo="{self.titulo}", rota_id={self.rota_id})'
    
    def __str__(self):
        return f"Título: {self.titulo or '[sem título]'}\nTexto: {self.texto or '[sem conteúdo]'}"
