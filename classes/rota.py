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
    parent_id = Column(Integer, ForeignKey("rotas.id"), nullable=True)  # Rota pai (hierarquia)
    caminho = Column(String(255), default="/", nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com URL e Conteúdo
    url = relationship("Url", back_populates="rotas")
    conteudo = relationship("Conteudo", back_populates="rota", uselist=False, cascade="all, delete-orphan")
    
    # Auto-relacionamento para hierarquia
    parent = relationship("Rota", remote_side=[id], backref="filhas", foreign_keys=[parent_id])
    
    def __repr__(self):
        return f'Rota(id={self.id}, caminho="{self.caminho}", url_id={self.url_id}, parent_id={self.parent_id})'
    
    def __str__(self):
        return f"Rota: {self.caminho}"
    
    def obter_caminho_completo(self) -> str:
        """Retorna o caminho completo da rota, considerando a hierarquia"""
        # Se tem um mapa injetado (vem de GerenciadorRotas), usar
        if hasattr(self, '__mapa_rotas__'):
            from classes.validators import GerenciadorRotas
            return GerenciadorRotas._obter_caminho_completo_com_mapa(self, self.__mapa_rotas__)
        
        # Se não tem pai, retorna o caminho como está
        if self.parent_id is None:
            return self.caminho
        
        # Se tem pai, constrói o caminho de forma iterativa (não recursiva) para evitar DetachedInstanceError
        caminhos = [self.caminho]
        rota_atual = self
        
        while rota_atual.parent_id is not None:
            # Tentar carregar parent - se detached, pode falhar
            try:
                rota_atual = rota_atual.parent
                if rota_atual is None:
                    break
                caminhos.insert(0, rota_atual.caminho)
            except:
                # Se falhar de carregar (detached), parar
                break
        
        # Juntar caminhos
        caminho_completo = "/".join(caminhos)
        # Limpar barras duplas e garantir barra inicial
        caminho_completo = "/" + caminho_completo.lstrip("/").replace("//", "/")
        return caminho_completo
    

    def obter_rotas_filhas_diretas(self):
        """Retorna rotas filhas diretas usando mapa injetado ou filhas pré-carregadas"""

        if hasattr(self, '__mapa_rotas__'):
            mapa = self.__mapa_rotas__
            return [mapa[r_id] for r_id in mapa if mapa[r_id].parent_id == self.id]
        
        if hasattr(self, '_filhas_carregadas'):
            return [r for r in self._filhas_carregadas if r.parent_id == self.id]
        
        # Retorna lista vazia para evitar lazy load
        return []

