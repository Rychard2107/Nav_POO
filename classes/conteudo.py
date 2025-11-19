# classe conteudo
class Conteudo:

    def __init__(self, titulo: str = "", texto: str = ""):
        self.titulo = titulo
        self.texto = texto

    def __repr__(self):
        return f'Conteúdo: titulo={self.titulo}, texto={self.texto}'
    
