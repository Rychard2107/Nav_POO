# 🌐 Navegador de URLs com SQLAlchemy

Sistema completo de navegador de URLs com persistência em banco de dados SQLite usando SQLAlchemy ORM.

## 🎯 Características

- **ORM com SQLAlchemy**: Classes mapeadas para tabelas SQLite
- **Validação de URLs**: Formato rigoroso (nome.domínio)
- **Gerenciamento de Rotas**: Adicionar rotas customizadas a cada URL
- **Conteúdo Persistente**: Armazenar título e texto em cada rota
- **Interface Rich**: Layout intuitivo com histórico e conteúdo

## 📁 Estrutura do Projeto

```
Nav_POO/
├── config.py                 # Configuração SQLAlchemy e banco de dados
├── main.py                   # Aplicação principal do navegador
├── teste_banco.py            # Script de testes automatizados
├── classes/
│   ├── __init__.py
│   ├── url.py               # Modelo de URL (SQLAlchemy)
│   ├── rota.py              # Modelo de Rota (SQLAlchemy)
│   ├── conteudo.py          # Modelo de Conteúdo (SQLAlchemy)
│   └── validators.py        # Validadores e gerenciadores
├── funcoes/
│   ├── __init__.py
│   ├── comands.py           # Validação de comandos
│   └── interface.py         # Interface e processamento
└── navigator.db             # Banco de dados SQLite (criado automaticamente)
```

## 🗄️ Modelos do Banco de Dados

### Urls
```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY,
    caminho VARCHAR(255) UNIQUE NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Rotas
```sql
CREATE TABLE rotas (
    id INTEGER PRIMARY KEY,
    url_id INTEGER NOT NULL FOREIGN KEY,
    caminho VARCHAR(255) NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Conteudos
```sql
CREATE TABLE conteudos (
    id INTEGER PRIMARY KEY,
    rota_id INTEGER NOT NULL FOREIGN KEY,
    titulo VARCHAR(255),
    texto TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## 🚀 Como Usar

### 1) Iniciar a aplicação

```bash
cd "/home/rychard/Área de Trabalho/Projetos/Nav_POO"
source venv/bin/activate
python main.py
```

### 2) Comandos Disponíveis

#### Digitar URLs
```
>>> google.com
>>> ifpb.org
>>> github.io
```

#### Comandos Especiais

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `#help` | Mostra todos os comandos | `#help` |
| `#add` | Validar e adicionar URL ao banco | `#add` → digitar URL |
| `#add_rota` | Adicionar rota à URL atual | `#add_rota` → `/api` |
| `#show_urls` | Listar todas as URLs no banco | `#show_urls` |
| `#clear_history` | Limpar histórico da sessão | `#clear_history` |
| `#back` | Voltar no histórico | `#back` |
| `#sair` | Sair do programa | `#sair` |

### 3) Exemplo de Uso Completo

```bash
>>> google.com              # Carrega google.com do banco (ou cria se não existir)
>>> #add_rota              # Adiciona rota à google.com
Digite o caminho: /search
Deseja adicionar conteúdo? (s/n): s
Título do conteúdo: Search Engine
Texto do conteúdo: Google search page
>>> #show_urls             # Mostra todas as URLs
>>> #sair                  # Sair
```

## ✅ Validação de URLs

URLs válidas devem ter:
- **Formato**: `nome.dominio`
- **Nome**: apenas letras, números e hífen
- **Domínios válidos**: `.com`, `.org`, `.br`, `.gov`, `.edu`, `.net`, `.io`

Exemplos válidos:
- ✓ google.com
- ✓ ifpb.org
- ✓ github-users.io

Exemplos inválidos:
- ✗ google (sem domínio)
- ✗ test@.com (caractere inválido)
- ✗ site.xyz (domínio não reconhecido)

## 🔧 Dependências

```bash
pip install sqlalchemy rich
```

## 📊 Testes

Execute o script de testes para validar todas as funcionalidades:

```bash
python teste_banco.py
```

Testa:
- ✓ Validação de URLs
- ✓ Criação de URLs no banco
- ✓ Listagem de URLs
- ✓ Adição de rotas
- ✓ Gerenciamento de conteúdo

## 🏗️ Arquitetura

### Fluxo de Dados

```
Entrada do Usuário
        ↓
Validação (ValidadorUrl)
        ↓
Banco de Dados (SQLAlchemy)
        ↓
Interface (Rich Console)
        ↓
Exibição
```

### Relacionamentos

```
Url (1) ←→ (N) Rota ←→ (1) Conteudo
```

- Uma URL pode ter múltiplas rotas
- Cada rota pode ter um conteúdo
- Todos os dados são persistidos no SQLite

## 📝 Exemplos de Código

### Validar e criar URL

```python
from classes import ValidadorUrl

url_obj, erro = ValidadorUrl.criar_ou_obter("google.com")
if erro:
    print(f"Erro: {erro}")
else:
    print(f"URL criada: {url_obj.caminho} (ID: {url_obj.id})")
```

### Adicionar rota

```python
from classes import GerenciadorRotas

rota, erro = GerenciadorRotas.adicionar_rota(
    url_id=1,
    caminho_rota="/api",
    titulo="API Root",
    texto="Endpoint raiz"
)
```

### Consultar do banco

```python
from config import get_db
from classes import Url

db = get_db()
urls = db.query(Url).all()
for url in urls:
    print(f"{url.caminho}: {len(url.rotas)} rotas")
db.close()
```

## 🐛 Troubleshooting

### Erro: "Import sqlalchemy could not be resolved"
```bash
pip install sqlalchemy
```

### Erro: "Database is locked"
- Feche outras instâncias do programa
- Delete `navigator.db` e deixe recriar

### URLs não aparecem após adicionar
- Verifique se digitou o domínio válido
- Use `#show_urls` para confirmar

## 📈 Melhorias Futuras

- [ ] Buscar URLs pelo nome
- [ ] Editar conteúdo de rotas existentes
- [ ] Exportar histórico para arquivo
- [ ] Backup automático do banco
- [ ] Suporte a múltiplas contas/usuários
- [ ] API REST para acesso remoto

## 👨‍💻 Autor

Desenvolvido com ❤️ usando SQLAlchemy + Rich
