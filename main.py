from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from funcoes import command_is_valid, criar_tabela_historico, processar_comando, processar_url
from config import init_db
from rich.text import Text


# Inicializar banco de dados
init_db()

# Configuração
console = Console()
historic_urls: list = []  # Lista de tuplas: [(url, rota_completa), ...]
conteudo_atual = ""
url_atual = None
rota_atual = None
comando = ""

# Tela de boas-vindas
console.clear()

console.print(Panel(
    "🌐 Navegador de URLs\nDigite uma URL (ex: google.com) ou um comando (#help)",
    title="Navegador",
    style="bold blue"
))

# Loop principal
while True:
    console.clear()
    
    url_text = Text()
    
    url_text.append("Você está aqui:\n", style="bold cyan")

    if url_atual is None:
        url_text.append("Nenhuma URL no momento", style="dim yellow")
    else:
        localizacao = url_atual
        if rota_atual and rota_atual.obter_caminho_completo() != "/":
            localizacao += rota_atual.obter_caminho_completo()
        url_text.append(localizacao, style="bold green")

    console.print(
        Panel(
            url_text,
            title="URL Atual",
            border_style="bold blue"
        )
    )

    # Layout principal: topo + main
    layout = Layout(name="main")
    layout.split_column(
        Layout(name="top", size=4),
        Layout(name="main")
    )
    
    # Topo com input dentro de panel
    entrada_text = Text()
    entrada_text.append("Digite URL ou comando (ex: google.com, /tsi, #help, #add_rota /tsi/professores):\n", style="bold cyan")
    entrada_text.append("(#sair para sair do programa)", style="dim yellow")
    layout["top"].update(Panel(entrada_text, title="Entrada", style="magenta", border_style="bold magenta"))
    
    # Main: histórico (esquerda) e conteúdo (direita)
    layout["main"].split_row(
        Layout(Panel(criar_tabela_historico(historic_urls), title="Menu - Histórico", style="blue"), name="left"),
        Layout(Panel(
            Text(conteudo_atual or "Digite uma URL ou comando para começar..."),
            title="Conteúdo",
            style="green"
        ), name="right")
    )

    console.print(layout)
    
    try:
        # Capturar entrada do usuário
        entrada = console.input(">>> ").strip()
        if entrada == "#sair":
            console.print(Panel("Até logo!", style="yellow"))
            break
        elif entrada == "#back":
            if len(historic_urls) < 2:
                conteudo_atual = "✗ Nenhuma URL anterior no histórico"
                continue
            # Remover a entrada atual do histórico
            historic_urls.pop()
            # Recuperar a entrada anterior
            url_anterior, rota_anterior = historic_urls[-1]
            # Se for uma rota, navegar para a rota
            if rota_anterior != "/":
                conteudo_atual, url_obj, rota_obj, _ = processar_url(rota_anterior, historic_urls)
            else:
                conteudo_atual, url_obj, rota_obj, _ = processar_url(url_anterior, historic_urls)
            
            if url_obj and rota_obj:
                url_atual = url_obj.caminho
                rota_atual = rota_obj
            else:
                url_atual = None
                rota_atual = None
            continue
        
        if not entrada:
            conteudo_atual = "✗ Nenhum comando digitado"
            continue

        
        # Dividir comando e argumentos
        partes = entrada.split(maxsplit=1)
        comando = partes[0]
        nova_url = partes[1] if len(partes) > 1 else ""
        
        # Verificar se é comando
        if command_is_valid(comando):
            conteudo_atual = processar_comando(comando, historic_urls, url_atual, nova_url)
            
            # Se foi processada uma URL com sucesso, atualizar url_atual e rota_atual
            if comando in ["#add", "#add_rota"] and "✓" in conteudo_atual:
                if comando == "#add":
                    url_atual = nova_url
                    rota_atual = None
        
        # Verificar se é rota (começa com /)
        elif comando.startswith("/"):
            conteudo_atual, url_obj, rota_obj, _ = processar_url(comando, historic_urls)
            if url_obj and rota_obj:
                url_atual = url_obj.caminho
                rota_atual = rota_obj
                # Obter o caminho completo da rota
                caminho_rota_completo = rota_obj.obter_caminho_completo()
                # Adicionar ao histórico apenas se for diferente da última entrada
                nova_entrada = (url_obj.caminho, caminho_rota_completo)
                if not historic_urls or historic_urls[-1] != nova_entrada:
                    historic_urls.append(nova_entrada)
        
        # Caso contrário, tratar como URL
        else:
            conteudo_atual, url_obj, rota_obj, _ = processar_url(comando, historic_urls)
            # Atualizar URL atual
            if url_obj and rota_obj:
                url_atual = url_obj.caminho
                rota_atual = rota_obj
                # Obter o caminho completo da rota
                caminho_rota_completo = rota_obj.obter_caminho_completo()
                # Adicionar ao histórico apenas se for diferente da última entrada
                nova_entrada = (url_obj.caminho, caminho_rota_completo)
                if not historic_urls or historic_urls[-1] != nova_entrada:
                    historic_urls.append(nova_entrada)

    
    except KeyboardInterrupt:
        console.print("\nPrograma interrompido", style="red")
        break
    
