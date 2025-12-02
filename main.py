from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from funcoes import comand_is_valid, criar_tabela_historico, processar_comando, processar_url
from config import init_db

# Inicializar banco de dados
init_db()

# Configuração
console = Console()
historic_urls: list = []
conteudo_atual = ""
url_atual = None
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
    
    # Layout principal: topo + main
    layout = Layout(name="main")
    layout.split_column(
        Layout(name="top", size=4),
        Layout(name="main")
    )
    
    # Topo com input dentro de panel
    entrada_text = Text()
    entrada_text.append("Digite URL ou comando (ex: google.com, #help, #add_rota):\n", style="bold cyan")
    entrada_text.append("(#sair para sair do programa)", style="dim yellow")
    layout["top"].update(Panel(entrada_text, title="🔍 Entrada", style="magenta", border_style="bold magenta"))
    
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
    
    # Capturar entrada do usuário
    try:
        comando = console.input(">>> ").strip()
        
        if not comando:
            console.print("Nenhum comando digitado")
            continue
        
        if comando == "#sair":
            console.print(Panel("Até logo!", style="yellow"))
            break
        
        # Verificar se é comando
        if comand_is_valid(comando):
            conteudo_atual = processar_comando(comando, historic_urls, url_atual)
            # Atualizar URL atual após comandos
            if historic_urls:
                url_atual = historic_urls[-1]
        
        else:
            # Tratar como URL
            conteudo_atual = processar_url(comando, historic_urls)
            # Atualizar URL atual
            if historic_urls:
                url_atual = historic_urls[-1]

    
    except KeyboardInterrupt:
        console.print("\nPrograma interrompido", style="red")
        break
    
