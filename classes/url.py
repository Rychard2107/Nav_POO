# url.py - Modelo de URL com SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class Url(Base):
    """Modelo de URL armazenado no banco de dados"""
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    caminho = Column(String(255), unique=True, nullable=False, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Rotas
    rotas = relationship("Rota", back_populates="url", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'Url(id={self.id}, caminho="{self.caminho}")'
    
    def __str__(self):
        return f"URL: {self.caminho}"
    
    def adicionar_rota(self, caminho_rota: str, titulo: str = "", texto: str = ""):
        """Adiciona uma nova rota para esta URL"""
        from classes.rota import Rota
        from classes.conteudo import Conteudo
        
        # Verificar se rota já existe
        for rota in self.rotas:
            if rota.caminho == caminho_rota:
                return rota
        
        # Criar nova rota
        nova_rota = Rota(caminho=caminho_rota, url_id=self.id)
        
        # Criar conteúdo se houver
        if titulo or texto:
            novo_conteudo = Conteudo(titulo=titulo, texto=texto)
            nova_rota.conteudo = novo_conteudo
        
        self.rotas.append(nova_rota)
        return nova_rota