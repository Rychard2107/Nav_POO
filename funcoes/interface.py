from classes import ValidadorUrl, GerenciadorRotas, Url
from rich.table import Table
from rich.console import Console
from config import get_db, init_db
import re

console = Console()

def criar_tabela_historico(urls: list) -> Table:
    """Cria tabela com histórico de URLs"""
    table = Table(title="Histórico", show_header=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("URL", style="magenta")
    
    if not urls:
        table.add_row("--", "Nenhuma URL visitada")
    else:
        for idx, url_item in enumerate(urls, 1):
            table.add_row(str(idx), url_item)
    
    return table


def processar_url(url_str: str, historic_urls: list):
    """
    Processa uma URL: valida e carrega do banco
    Retorna: string formatada com conteúdo da URL
    """
    try:
        # Validar URL e carregar com relacionamentos
        url_obj, erro = ValidadorUrl.criar_ou_obter(url_str)
        
        if erro:
            return f"✗ {erro}"
        
        # Adicionar ao histórico
        if url_obj.caminho not in historic_urls:
            historic_urls.append(url_obj.caminho)
        
        # Formatar resposta (url_obj está detached mas com dados carregados)
        resposta = f"Url: {url_obj.caminho}\n"
        resposta += f"✓ URL carregada\n"
        
        # Acessar rotas e conteúdo (já carregados na memória)
        try:
            num_rotas = len(url_obj.rotas) if url_obj.rotas else 0
            resposta += f"Rotas: {num_rotas}\n\n"
            
            # Listar rotas com conteúdo
            if url_obj.rotas:
                resposta += "Rotas disponíveis:\n"
                for rota in url_obj.rotas:
                    conteudo_info = ""
                    # Conteúdo já foi carregado com joinedload, acesso seguro
                    if rota.conteudo:
                        titulo = rota.conteudo.titulo or '[sem título]'
                        conteudo_info = f" - {titulo}"
                    resposta += f"  • {rota.caminho}{conteudo_info}\n"
        except Exception as e:
            resposta += f"(Erro ao listar rotas: {str(e)})\n"
        
        return resposta
    
    except Exception as e:
        return f"✗ Erro ao processar URL: {str(e)}"


def processar_comando(cmd: str, historic_urls: list, url_atual=None):
    """
    Processa os comandos do sistema
    Retorna: string formatada com resultado do comando
    """
    
    if cmd == "#help":
        return """Comandos Disponíveis:
URLs e Rotas:
  <url>             - Digitar uma URL (ex: google.com)
  #add              - Validar e adicionar URL ao banco
  #add_rota         - Adicionar rota à URL atual
  
Histórico:
  #clear_history    - Limpar histórico
  #back             - Voltar para URL anterior
  
Sistema:
  #help             - Mostrar esta ajuda
  #sair             - Sair do programa"""
    
    
    elif cmd == "#add":
        url_input = console.input("Digite a URL para adicionar: ").strip()
        url_obj, erro = ValidadorUrl.criar_ou_obter(url_input)
        
        if erro:
            return f"✗ {erro}"
        
        if url_input not in historic_urls:
            historic_urls.append(url_input)
        
        return f"✓ URL '{url_obj.caminho}' adicionada com sucesso!"
    
    elif cmd == "#add_rota":
        if url_atual is None:
            return "⚠ Nenhuma URL selecionada. Use uma URL antes de adicionar rotas."
        try:
            db = get_db()

            
            url_normalizada = re.sub(r"^(http(s)?://)?(www\.)?", "", url_atual.strip().lower())
            url_normalizada = url_normalizada.split('/', 1)[0]
            url_obj = db.query(Url).filter(Url.caminho == url_normalizada).first()
            
            if not url_obj:
                return f"✗ URL não encontrada (busca por: {url_normalizada})"
            
            # Solicitar caminho da rota
            rota_path = console.input("Caminho da rota (ex: /api): ").strip()
            
            if not rota_path:
                return "Operação cancelada"
            
            # Solicitar conteúdo
            adicionar_conteudo = console.input("Deseja adicionar conteúdo? (s/n): ").strip().lower()
            
            titulo = ""
            texto = ""
            
            if adicionar_conteudo == "s":
                titulo = console.input("Título do conteúdo: ").strip()
                texto = console.input("Texto do conteúdo: ").strip()
            
            # Adicionar rota
            nova_rota, erro = GerenciadorRotas.adicionar_rota(url_obj.id, rota_path, titulo, texto)
            
            if erro and "já existe" not in erro:
                return f"✗ {erro}"
            
            return f"✓ Rota '{rota_path}' adicionada à URL '{url_atual}'!"
        
        except Exception as e:
            return f"✗ Erro ao adicionar rota: {str(e)}"
        finally:
            db.close()
    
    
    else:
        return f"✗ Comando desconhecido: {cmd}"
