from classes import ValidadorUrl, GerenciadorRotas, Url, Rota
from rich.table import Table
from rich.console import Console
from config import get_db, init_db
from sqlalchemy.orm import selectinload
import re


console = Console()

def criar_tabela_historico(historico: list) -> Table:
    """Cria tabela com histórico de URLs e rotas
    
    historico é uma lista de tuplas: [(url, rota_caminho_completo), ...]
    """
    table = Table(title="Histórico", show_header=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("URL", style="magenta")
    table.add_column("Rota", style="yellow")
    
    if not historico:
        table.add_row("--", "Nenhuma URL visitada", "--")
    else:
        for idx, item in enumerate(historico, 1):
            if isinstance(item, tuple):
                url_item, rota_item = item
            else:
                # Compatibilidade com strings antigas
                url_item = item
                rota_item = "/"
            table.add_row(str(idx), url_item, rota_item)
    
    return table




def processar_url(url_str: str, historico: list):
    """Processa uma URL com EAGER LOADING completo para hierarquia
    
    historico é uma lista de tuplas: [(url, rota_caminho_completo), ...]
    """
    try:
        if url_str.startswith("/"):
            # ROTA INTERNA
            if not historico:
                return "✗ Nenhuma URL selecionada", None, None, None
            
            # Extrair URL do último item do histórico
            url_do_historico = historico[-1][0] if isinstance(historico[-1], tuple) else historico[-1]
            url_normalizada = re.sub(r"^(http(s)?://)?(www\.)?", "", url_do_historico.strip().lower())
            url_normalizada = url_normalizada.split('/', 1)[0]
            
            db = get_db()
            url_obj = db.query(Url).filter(Url.caminho == url_normalizada).first()
            db.close()
            
            if not url_obj:
                return f"✗ URL base não encontrada", None, None, None
            
            # CORREÇÃO: Query com selectinload RECURSIVO para hierarquia
            db = get_db()
            rota_obj = db.query(Rota).options(
                selectinload(Rota.filhas).selectinload(Rota.filhas),  # 2 níveis de filhas
                selectinload(Rota.parent),
                selectinload(Rota.conteudo)
            ).filter(
                Rota.url_id == url_obj.id
            ).all()
            
            # Criar mapa e encontrar rota pelo caminho
            mapa_rotas = {r.id: r for r in rota_obj}
            rota_obj = None
            
            # Normalizar url_str para busca (garantir que "/" permanece como "/")
            url_busca = url_str.rstrip('/') if url_str != "/" else "/"
            
            for r in mapa_rotas.values():
                caminho_completo = GerenciadorRotas._obter_caminho_completo_com_mapa(r, mapa_rotas)
                if caminho_completo == url_busca:
                    rota_obj = r
                    break
            
            db.expunge_all()
            db.close()
            
            if not rota_obj:
                return f"✗ Rota '{url_str}' não encontrada", None, None, None
            
            # Injetar mapa na rota
            rota_obj.__mapa_rotas__ = mapa_rotas
            rota_obj._filhas_carregadas = list(rota_obj.filhas)
            
            return formatar_rota(url_obj, rota_obj, mapa_rotas), url_obj, rota_obj, mapa_rotas
        
        # URL COMPLETA
        url_obj, erro = ValidadorUrl.obter(url_str)
        if erro:
            return f"✗ {erro}", None, None, None
        
        # Rota padrão "/" com filhas carregadas
        db = get_db()
        rota_obj = db.query(Rota).options(
            selectinload(Rota.filhas).selectinload(Rota.filhas),
            selectinload(Rota.parent),
            selectinload(Rota.conteudo)
        ).filter(
            Rota.url_id == url_obj.id,
            Rota.caminho == "/"
        ).first()
        
        todas_rotas = db.query(Rota).options(
            selectinload(Rota.filhas),
            selectinload(Rota.conteudo)
        ).filter(Rota.url_id == url_obj.id).all()
        
        mapa_rotas = {r.id: r for r in todas_rotas}
        db.expunge_all()
        db.close()
        
        if not rota_obj:
            return f"✗ Rota padrão não encontrada", url_obj, None, None
        
        rota_obj.__mapa_rotas__ = mapa_rotas
        rota_obj._filhas_carregadas = list(rota_obj.filhas)
        
        return formatar_rota(url_obj, rota_obj, mapa_rotas), url_obj, rota_obj, mapa_rotas
    
    except Exception as e:
        return f"✗ Erro: {str(e)}", None, None, None


def formatar_rota(url_obj, rota_obj, mapa_rotas=None) -> str:
    """Formata a exibição de uma rota
    
    mapa_rotas é um dicionário {rota_id: rota} para construir caminhos completos
    """

    
    resposta = f"URL: {url_obj.caminho}\n"
    
    # Construir caminho completo da rota atual
    if mapa_rotas:
        caminho_rota = GerenciadorRotas._obter_caminho_completo_com_mapa(rota_obj, mapa_rotas)
    else:
        caminho_rota = rota_obj.obter_caminho_completo()
    
    resposta += f"Rota: {caminho_rota}\n"
    resposta += f"✓ Carregado com sucesso\n\n"
    
    # Listar subrotas disponíveis
    rotas_filhas = rota_obj.obter_rotas_filhas_diretas()
    
    if rotas_filhas:
        resposta += "Rotas disponíveis:\n"
        for rota_filha in rotas_filhas:
            # Construir caminho completo da filha
            if mapa_rotas:
                caminho_filha = GerenciadorRotas._obter_caminho_completo_com_mapa(rota_filha, mapa_rotas)
            else:
                caminho_filha = rota_filha.obter_caminho_completo()
            
            conteudo_info = ""
            if rota_filha.conteudo:
                titulo = rota_filha.conteudo.titulo or '[sem título]'
                conteudo_info = f" - {titulo}"
            resposta += f"  • {caminho_filha}{conteudo_info}\n"
    else:
        # Se não há filhas, mostrar conteúdo da rota atual
        if rota_obj.conteudo:
            resposta += f"Conteúdo:\n"
            resposta += f"  Título: {rota_obj.conteudo.titulo or '[sem título]'}\n"
            resposta += f"  Texto: {rota_obj.conteudo.texto or '[sem conteúdo]'}\n"
        else:
            resposta += "Nenhuma subrota ou conteúdo disponível\n"
    
    return resposta


def processar_comando(cmd: str, historic_urls: list, url_atual=None, nova_url=None) -> str:
    
    """
    Processa os comandos do sistema
    Retorna: string formatada com resultado do comando
    """
    
    if cmd == "#help":
        return """Comandos Disponíveis:
URLs e Rotas:
  <url>             - Digitar uma URL (ex: google.com)
  /<rota>           - Navegar para rota da URL atual (ex: /tsi)
  #add <url>        - Validar e adicionar URL ao banco (ex: #add ifpb.edu.br)
  #add_rota <rota>  - Adicionar rota à URL atual (ex: #add_rota /tsi/professores)
  
Histórico:
  #clear_history    - Limpar histórico
  #back             - Voltar para URL anterior
  
Sistema:
  #help             - Mostrar esta ajuda
  #show_urls        - Mostrar todas URLs cadastradas
  #sair             - Sair do programa"""
    
    
    elif cmd == "#add":
        if not nova_url:
            return "✗ Use: #add <url> (ex: #add google.com)"
        
        url_obj, erro = ValidadorUrl.criar(nova_url)
        
        if erro:
            return f"✗ {erro}"
        
        return f"✓ URL '{url_obj.caminho}' adicionada com sucesso!"
    
    elif cmd == "#add_rota":
        if url_atual is None:
            return "✗ Nenhuma URL selecionada. Use uma URL antes de adicionar rotas."
        
        if not nova_url:
            return "✗ Use: #add_rota <caminho> (ex: #add_rota /tsi/professores)"
        
        try:
            db = get_db()
            
            url_normalizada = re.sub(r"^(http(s)?://)?(www\.)?", "", url_atual.strip().lower())
            url_normalizada = url_normalizada.split('/', 1)[0]
            url_obj = db.query(Url).filter(Url.caminho == url_normalizada).first()
            
            if not url_obj:
                db.close()
                return f"✗ URL não encontrada (busca por: {url_normalizada})"
            
            # Solicitar conteúdo (opcional)
            adicionar_conteudo = console.input("Deseja adicionar conteúdo? (s/n): ").strip().lower()
            
            titulo = ""
            texto = ""
            
            if adicionar_conteudo == "s":
                titulo = console.input("Título do conteúdo: ").strip()
                texto = console.input("Texto do conteúdo: ").strip()
            
            # Adicionar rota
            nova_rota, erro = GerenciadorRotas.adicionar_rota(url_obj.id, nova_url, titulo, texto)
            
            if erro and "já existe" not in erro:
                db.close()
                return f"✗ {erro}"
            
            db.close()
            return f"✓ Rota '{nova_url}' adicionada à URL '{url_atual}'!"
        
        except Exception as e:
            db.close()
            return f"✗ Erro ao adicionar rota: {str(e)}"
    
    elif cmd == "#show_urls":
        db = get_db()
        try:
            urls = db.query(Url).all()
            if not urls:
                return "Nenhuma URL cadastrada"
            
            resposta = "URLs cadastradas:\n"
            for url in urls:
                resposta += f"  • {url.caminho} ({len(url.rotas)} rotas)\n"
            return resposta
        finally:
            db.close()
    
    elif cmd == "#clear_history":
        if hasattr(historic_urls, 'clear'):
            historic_urls.clear()
        return "✓ Histórico limpo"
    
    
