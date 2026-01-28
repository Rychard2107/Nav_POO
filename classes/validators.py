import re
from config import get_db, init_db
from classes.url import Url
from classes.rota import Rota
from classes.conteudo import Conteudo
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload



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
    def obter(cls, url_str: str) -> tuple[Url, str]:
        """
        Obtém uma URL do banco de dados.
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
            # Buscar URL
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
            
            db.close()
            return None, "URL não encontrada"

        except Exception as e:
            db.rollback()
            db.close()
            return None, f"Erro ao buscar URL: {str(e)}"

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
                        # 2. Criação no DB
                        url_obj, erro_db = cls.criar(url_str)
                        
                        if url_obj:
                            # print(f"Salva: {url_str} (Normalizada: {url_obj.caminho})")
                            estatisticas["validas_salvas"] += 1
                        else:
                            # print(f"Erro DB ao salvar {url_str}: {erro_db}")
                            estatisticas["erros_db"] += 1
                    else:
                        # print(f"Inválida: {url_str} ({erro_validacao})")
                        estatisticas["invalidas"] += 1

        except FileNotFoundError:
            print(f"ERRO: Arquivo '{nome_arquivo}' não encontrado.")
        except Exception as e:
            print(f"ERRO INESPERADO: {str(e)}")
            
        return estatisticas

    @classmethod
    def criar(cls, url_str: str) -> tuple[Url, str]:
        valido, erro = cls.validar(url_str)
        if not valido:
            return None, erro
    
        url_normalizada = url_str.strip().lower()
        url_normalizada = re.sub(r"^(http(s)?://)?(www\.)?", "", url_normalizada)
        url_normalizada = url_normalizada.split('/', 1)[0]
        db = get_db()
        # Criar nova URL
        try:
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


# ---
# Gerenciador de Rotas
# ---

class GerenciadorRotas:
    """Gerencia rotas de URLs"""
    
    @classmethod
    def obter_rota(cls, url_obj: Url, caminho_rota: str) -> tuple:
        """Busca rota com eager loading completo"""
        if not caminho_rota.startswith("/"):
            caminho_rota = "/" + caminho_rota
        
        caminho_normalizado = caminho_rota.rstrip("/") if len(caminho_rota) > 1 else "/"
        
        db = get_db()
        try:
            # CARREGAR TUDO DE UMA VEZ com selectinload
            rotas = db.query(Rota).options(
                selectinload(Rota.filhas).selectinload(Rota.filhas),
                selectinload(Rota.parent),
                selectinload(Rota.conteudo)
            ).filter(Rota.url_id == url_obj.id).all()
            
            mapa_rotas = {r.id: r for r in rotas}
            
            # Encontrar rota pelo caminho completo
            for r in rotas:
                caminho_completo = cls._obter_caminho_completo_com_mapa(r, mapa_rotas)
                if caminho_completo == caminho_normalizado:
                    r.__mapa_rotas__ = mapa_rotas
                    r._filhas_carregadas = list(r.filhas)  # Cache local
                    db.expunge_all()
                    db.close()
                    return r, ""
            
            db.close()
            return None, f"Rota '{caminho_rota}' não encontrada"
        
        except Exception as e:
            db.rollback()
            db.close()
            return None, f"Erro: {str(e)}"

    
    @staticmethod
    def _obter_caminho_completo_com_mapa(rota: Rota, mapa_rotas: dict) -> str:
        """Constrói o caminho completo usando um mapa de rotas"""
        if rota.parent_id is None:
            return rota.caminho
        
        caminhos = [rota.caminho]
        rota_atual_id = rota.parent_id
        
        while rota_atual_id is not None:
            rota_pai = mapa_rotas.get(rota_atual_id)
            if rota_pai is None:
                break
            caminhos.insert(0, rota_pai.caminho)
            rota_atual_id = rota_pai.parent_id
        
        # Juntar caminhos
        caminho_completo = "/".join(caminhos)
        # Limpar barras duplas e garantir barra inicial
        caminho_completo = "/" + caminho_completo.lstrip("/").replace("//", "/")
        return caminho_completo
    
    @classmethod
    def adicionar_rota(cls, url_id: int, caminho_rota: str, titulo: str = "", texto: str = "") -> tuple[Rota, str]:
        """
        Adiciona uma rota a uma URL com suporte a hierarquia.
        Exemplo: adicionar "/tsi/professores" quando "/tsi" já existe
        Retorna: (rota_obj, mensagem_erro)
        """
        db = get_db()
        
        try:
            # Validar caminho da rota
            if not caminho_rota.startswith("/"):
                return None, "Rota deve começar com '/'"
            
            # Normalizar caminho
            caminho_rota = caminho_rota.rstrip("/") if len(caminho_rota) > 1 else "/"
            
            # Obter URL
            url_obj = db.query(Url).filter(Url.id == url_id).first()
            if not url_obj:
                db.close()
                return None, "URL não encontrada"
            
            # Buscar todas as rotas existentes
            rotas_existentes = db.query(Rota).filter(Rota.url_id == url_id).all()
            
            # Criar mapa de rotas
            mapa_rotas = {r.id: r for r in rotas_existentes}
            
            # Verificar se rota já existe (verificar caminho completo)
            for rota in rotas_existentes:
                caminho_completo = cls._obter_caminho_completo_com_mapa(rota, mapa_rotas)
                if caminho_completo == caminho_rota:
                    db.close()
                    return rota, "Rota já existe"
            
            # Determinar rota pai
            parent_rota = None
            
            if caminho_rota == "/":
                # Rota raiz não tem pai
                parent_rota = None
            else:
                # Extrair caminho pai
                partes = caminho_rota.rsplit("/", 1)
                caminho_pai = partes[0] if partes[0] else "/"
                
                # Buscar rota pai
                for rota in rotas_existentes:
                    caminho_completo = cls._obter_caminho_completo_com_mapa(rota, mapa_rotas)
                    if caminho_completo == caminho_pai:
                        parent_rota = rota
                        break
                
                # Se não encontrou rota pai e não é nível 1, retornar erro
                if not parent_rota and caminho_pai != "/":
                    db.close()
                    return None, f"Rota pai '{caminho_pai}' não existe. Crie antes: #add_rota {caminho_pai}"
                
                # Se não encontrou e caminho_pai é "/", usar a rota raiz como pai
                if not parent_rota and caminho_pai == "/":
                    for rota in rotas_existentes:
                        if rota.caminho == "/" and rota.parent_id is None:
                            parent_rota = rota
                            break
            
            # Criar nova rota
            # Se tem rota pai, armazenar apenas a parte final
            if parent_rota:
                # Armazenar apenas a última parte do caminho
                partes = caminho_rota.rsplit("/", 1)
                caminho_salvo = partes[1] if partes[1] else "/"
                nova_rota = Rota(url_id=url_id, caminho=caminho_salvo, parent_id=parent_rota.id)
            else:
                nova_rota = Rota(url_id=url_id, caminho=caminho_rota, parent_id=None)
            
            # Adicionar conteúdo se houver
            if titulo or texto:
                novo_conteudo = Conteudo(titulo=titulo, texto=texto)
                nova_rota.conteudo = novo_conteudo
            
            db.add(nova_rota)
            db.commit()
            db.refresh(nova_rota)
            
            # Forçar carregamento de relacionamentos antes de desanexar
            _ = nova_rota.conteudo
            _ = nova_rota.parent  # Carregar parent
            _ = len(nova_rota.filhas)  # Carregar filhas
            
            db.expunge_all()
            db.close()
            
            return nova_rota, ""
        
        except Exception as e:
            db.rollback()
            db.close()
            return None, f"Erro ao adicionar rota: {str(e)}"
