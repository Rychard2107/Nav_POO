import re
from config import get_db, init_db
from classes.url import Url
from classes.rota import Rota
from classes.conteudo import Conteudo
from sqlalchemy.orm import joinedload

class ValidadorUrl:
    """Valida e processa URLs"""
    
    # Domínios válidos
    DOMINIOS_VALIDOS = ["com", "org", "br", "gov", "edu", "io", "net"]
    
    # Regex robusta para validar a URL completa: (http(s)?://)?(www\.)?{nome_dominio}.{tld}(/rota...)?
    REGEX_URL = re.compile(
        # Início da string
        r"^(http(s)?://)?"  
        # Opcional www.
        r"(www\.)?"         
        # Nome principal do domínio e possíveis subdomínios/estrutura
        r"([a-z0-9\-]+(\.[a-z0-9\-\.]+)*)"  
        # Ponto e o TLD (Top-Level Domain)
        r"\.(" + "|".join(DOMINIOS_VALIDOS) + r")" 
        # Rota/caminho opcional no final
        r"(/.*)?$", 
        re.IGNORECASE 
    )
    
    @classmethod
    def validar(cls, url_str: str) -> tuple[bool, str]:
        """
        Valida uma URL usando Expressão Regular (Regex) para checar prefixos e domínios.
        Retorna: (válido, mensagem_erro)
        """
        if not url_str:

            return False, "URL não pode ser vazia"
        
        url_str = url_str.strip()
        
        # Tenta corresponder a URL completa com a Regex
        if cls.REGEX_URL.fullmatch(url_str):
            return True, ""
        else:
            return False, f"URL inválida. Formato: [http(s)://][www.]{{nome}}.{'|'.join(cls.DOMINIOS_VALIDOS)}[/rota...]"

    
    @classmethod
    def criar_ou_obter(cls, url_str: str) -> tuple[Url, str]:
        """
        Cria ou obtém uma URL do banco.
        
        **Normaliza a URL** removendo prefixos (http/https/www) e rotas para salvar apenas
        o domínio principal (ex: youtube.com) como 'caminho' no banco.
        
        Retorna: (url_obj, mensagem_erro)
        """
        
        valido, erro = cls.validar(url_str)
        if not valido:
            return None, erro
    
        url_normalizada = url_str.strip().lower()
        url_normalizada = re.sub(r"^(http(s)?://)?(www\.)?", "", url_normalizada)
        url_normalizada = url_normalizada.split('/', 1)[0]
        db = get_db()
        
        try:
            # Buscar URL com eager loading de rotas e conteúdo
            url_obj = db.query(Url).options(
                joinedload(Url.rotas).joinedload(Rota.conteudo)
            ).filter(Url.caminho == url_normalizada).first()
            
            if url_obj:
                # Forçar carregamento dos dados enquanto sessão está aberta
                _ = len(url_obj.rotas)
                for rota in url_obj.rotas:
                    _ = rota.conteudo  # Acessa conteúdo para forçar carregamento
                
                # Expunge para desanexar da sessão com dados já carregados
                db.expunge_all()
                db.close()
                return url_obj, ""
            
            # Criar nova URL
            url_obj = Url(caminho=url_normalizada)
            
            # Criar rota padrão "/"
            rota_padrao = Rota(url_id=None, caminho="/")
            url_obj.rotas.append(rota_padrao)
            
            db.add(url_obj)
            db.commit()
            db.refresh(url_obj)
            
            # Forçar carregamento enquanto sessão está aberta
            _ = len(url_obj.rotas)
            for rota in url_obj.rotas:
                _ = rota.conteudo
            
            # Expunge para desanexar da sessão com dados já carregados
            db.expunge_all()
            db.close()
            
            return url_obj, ""
        
        except Exception as e:
            db.rollback()
            db.close()
            return None, f"Erro ao salvar URL: {str(e)}"

    @classmethod
    def popular_do_arquivo(cls, nome_arquivo: str) -> dict:
        """
        Lê um arquivo texto e tenta criar/obter URLs válidas no banco.
        Retorna um dicionário com estatísticas do processamento.
        """
        estatisticas = {
            "total_lidas": 0,
            "validas_salvas": 0,
            "invalidas": 0,
            "erros_db": 0
        }
        
        try:
            with open(nome_arquivo, 'r', encoding='utf-8') as f:
                print(f"Lendo o arquivo: {nome_arquivo}")
                for linha in f:
                    # Limpa a linha de espaços e quebras de linha
                    url_str = linha.strip()
                    if not url_str or url_str.startswith('#'):
                        continue # Pula linhas vazias ou comentários
                    
                    estatisticas["total_lidas"] += 1
                    
                    # 1. Validação do formato
                    valido, erro_validacao = cls.validar(url_str)
                    
                    if valido:
                        # 2. Criação/Obtenção no DB
                        url_obj, erro_db = cls.criar_ou_obter(url_str)
                        
                        if url_obj:
                            # print(f"✅ Salva: {url_str} (Normalizada: {url_obj.caminho})")
                            estatisticas["validas_salvas"] += 1
                        else:
                            # print(f"❌ Erro DB ao salvar {url_str}: {erro_db}")
                            estatisticas["erros_db"] += 1
                    else:
                        # print(f"❌ Inválida: {url_str} ({erro_validacao})")
                        estatisticas["invalidas"] += 1

        except FileNotFoundError:
            print(f"🚨 ERRO: Arquivo '{nome_arquivo}' não encontrado.")
        except Exception as e:
            print(f"🚨 ERRO INESPERADO: {str(e)}")
            
        return estatisticas


# ---
# Gerenciador de Rotas
# ---

class GerenciadorRotas:
    """Gerencia rotas de URLs"""
    
    @classmethod
    def adicionar_rota(cls, url_id: int, caminho_rota: str, titulo: str = "", texto: str = "") -> tuple[Rota, str]:
        """
        Adiciona uma rota a uma URL
        Retorna: (rota_obj, mensagem_erro)
        """
        db = get_db()
        
        try:
            # Validar caminho da rota
            if not caminho_rota.startswith("/"):
                return None, "Rota deve começar com '/'"
            
            # Obter URL
            url_obj = db.query(Url).filter(Url.id == url_id).first()
            if not url_obj:
                return None, "URL não encontrada"
            
            # Verificar se rota já existe
            rota_existente = db.query(Rota).filter(
                Rota.url_id == url_id,
                Rota.caminho == caminho_rota
            ).first()
            
            if rota_existente:
                return rota_existente, "Rota já existe"
            
            # Criar nova rota
            nova_rota = Rota(url_id=url_id, caminho=caminho_rota)
            
            # Adicionar conteúdo se houver
            if titulo or texto:
                novo_conteudo = Conteudo(titulo=titulo, texto=texto)
                nova_rota.conteudo = novo_conteudo
            
            db.add(nova_rota)
            db.commit()
            db.refresh(nova_rota)
            
            return nova_rota, ""
        
        except Exception as e:
            db.rollback()
            return None, f"Erro ao adicionar rota: {str(e)}"
        finally:
            db.close()
    
    @classmethod
    def obter_rotas(cls, url_id: int) -> list:
        """Obtém todas as rotas de uma URL"""
        db = get_db()
        try:
            rotas = db.query(Rota).filter(Rota.url_id == url_id).all()
            return rotas
        finally:
            db.close()