# Consulta de precipitação ANA — versão web local

Aplicação web local em Python/Flask para consultar precipitação por código da estação e período. Inclui máscara de data `DD/MM/AAAA`, tabela com rolagem, ordenação por cabeçalho (1º clique crescente, 2º decrescente, 3º remove a ordenação e restaura a ordem original) e exportação CSV compatível com Excel/LibreOffice.

## Requisitos
- Python 3.10 ou superior
- Acesso à internet para consultar a API da ANA

## Linux (Ubuntu/Debian)
No terminal, dentro da pasta do projeto:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:5000` no navegador. Para parar, volte ao terminal e pressione `Ctrl+C`.

## Windows
Instale Python 3.10+ e marque a opção de adicionar Python ao PATH. No Prompt de Comando, dentro da pasta do projeto:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

Abra `http://127.0.0.1:5000`.

## Segurança e funcionamento
O servidor escuta somente em `127.0.0.1`, portanto não fica exposto à rede local por padrão. Não há login porque o sistema é destinado ao uso individual neste computador. A consulta requer internet e depende do serviço da ANA. Os nomes dos campos XML podem variar conforme a resposta da estação; o aplicativo só mostra campos reconhecidos como chuva/precipitação e não interpreta nível ou vazão como chuva.
