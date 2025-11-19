from classes import Rota

class Url:
    def __init__(self, url: str = "localhost"):
        self.__caminho = url
        self.rotas = [Rota("/")]

    @property
    def caminho(self):
        return self.__caminho
    
    @caminho.setter
    def caminho(self, link: str):
        lista: list = ["com", "org"]
        try:
            site, dominio = link.split(".") 
            if dominio in lista:
                self.__caminho = site + dominio
            else:
                print('Erro: Domínios deve terminar ".com", ".org"')    
        except AttributeError:
            print("Erro: Tipo de variável deve ser string")
        except ValueError:
            print("Erro: Url deve conter 1 ponto")
            
    def add_rota(self, valor: str):
        if isinstance(valor, str) == False:
            print("Erro: A rota deve ser uma string")
        elif valor[0] != "/":
            print('Erro: A url deve conter pelo menos uma "/" no começo')

          
        
        
        



if __name__ == "__main__":
    print("###### TESTE DA URL ######")
    url1 = Url()
    print(url1.caminho)
    url1.caminho = "ifpb.com"