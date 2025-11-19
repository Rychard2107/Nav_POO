from classes.conteudo import Conteudo

class Rota:
    def __init__(self, rota: str, titulo_rota: str = "", texto_rota: str = ""):
        self.__rota = rota
        self.conteudo = Conteudo(titulo=titulo_rota, texto=texto_rota)

    @property
    def rota(self):
        return self.__rota
    
    @rota.setter
    def rota(self, valor: str):
        self.valor = valor
