# 🏠 ImobiliáriaPerto — Assistente IA Imobiliário

<div align="center">

![Status](https://img.shields.io/badge/status-online-22c55e?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-3b82f6?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-00e5bf?style=for-the-badge&logo=postgresql&logoColor=white)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Railway](https://img.shields.io/badge/Backend-Railway-7c3aed?style=for-the-badge&logo=railway&logoColor=white)

**Assistente inteligente de busca de imóveis com linguagem natural**  
Desenvolvido por [STR Software](https://www.strsoftware.com.br)

[🌐 Acessar Demo](https://imobiliaria-agente2.vercel.app) · [📚 Ver Tutorial](./tutorial/) · [🐛 Reportar Bug](https://github.com/extra1357/imobiliaria-agente/issues)

</div>

---

## ✨ Sobre o Projeto

O **ImobiliáriaPerto** é um assistente de busca de imóveis com **inteligência artificial** que entende linguagem natural. Em vez de preencher filtros, o usuário simplesmente escreve o que procura — e o sistema interpreta, consulta o banco de dados e retorna os resultados instantaneamente.

> *"Quero um apartamento em São Paulo até 600 mil com 2 quartos"*  
> → O assistente entende, filtra e retorna os imóveis disponíveis.

---

## 🚀 Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 🔍 **Busca Natural** | Entende frases como "casa em Salto até 400 mil" |
| 📊 **Análise de Preços** | Preço médio, mínimo e máximo por cidade |
| 📅 **Agendamento** | Lista imóveis disponíveis para visita |
| 👥 **Corretores** | Exibe equipe ativa com CRECI e contato |
| 💬 **WhatsApp** | Botão que monta a mensagem automaticamente |
| 🤖 **Sofia** | Consultora IA com avatar animado |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   USUÁRIO / BROWSER                  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           FRONTEND — Vercel                          │
│         imobiliaria-agente2.vercel.app               │
│              HTML + CSS + JavaScript                 │
└─────────────────────┬───────────────────────────────┘
                      │  POST /buscar
┌─────────────────────▼───────────────────────────────┐
│           BACKEND — Railway                          │
│     web-production-876cc.up.railway.app              │
│              Python + FastAPI                        │
│                                                      │
│  ┌─────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │intent_router│  │ busca IA │  │  tools/       │  │
│  │ detecta o   │→ │interpreta│→ │  price        │  │
│  │ que o user  │  │ linguagem│  │  schedule     │  │
│  │ quer        │  │ natural  │  │  brokers      │  │
│  └─────────────┘  └──────────┘  └───────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │  psycopg2
┌─────────────────────▼───────────────────────────────┐
│           BANCO DE DADOS — Neon                      │
│              PostgreSQL (nuvem)                      │
│   imoveis · corretores · leads · proprietarios      │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura do Projeto

```
imobiliaria-agente/
├── api.py                          # Servidor FastAPI principal
├── core/
│   └── db.py                       # Conexão com banco de dados
├── tools/
│   ├── property_search_advanced.py # Busca com linguagem natural
│   ├── intent_router.py            # Roteador de intenções
│   ├── price_analysis.py           # Análise de preço por cidade
│   ├── schedule_visit.py           # Agendamento de visitas
│   ├── broker_info.py              # Informações de corretores
│   └── property_tools.py           # Ferramentas de diagnóstico
├── web/
│   └── index.html                  # Interface do usuário
├── tutorial/
│   └── Tutorial_Assistente_IA.docx # Tutorial completo
├── .env                            # Variáveis de ambiente (não commitado)
├── .gitignore
├── requirements.txt
├── Procfile                        # Configuração Railway
└── vercel.json                     # Configuração Vercel
```

---

## ⚡ Como Rodar Localmente

### Pré-requisitos

- Python 3.12+
- PostgreSQL instalado
- Git

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/extra1357/imobiliaria-agente.git
cd imobiliaria-agente

# 2. Crie o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais

# 5. Inicie o servidor
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Arquivo .env

```env
DATABASE_URL=postgresql://usuario:senha@host/banco?sslmode=require
```

---

## 🧠 Como Funciona a Busca Natural

O sistema usa um interpretador próprio que extrai filtros do texto:

```
"apartamento em São Paulo até 600 mil com 2 quartos"
         ↓
{
  tipo:      "apartamento",
  cidade:    "São Paulo",
  preco_max: 600000,
  quartos:   2
}
         ↓
SELECT * FROM imoveis WHERE tipo ILIKE '%apartamento%'
AND cidade = 'São Paulo' AND preco <= 600000 AND quartos = 2
```

### Intenções reconhecidas

| Frase do usuário | Intenção detectada | Função |
|---|---|---|
| "apartamento em SP..." | `buscar` | `buscar_imoveis()` |
| "preço médio em Campinas" | `preco_medio` | `preco_medio_cidade()` |
| "quero agendar uma visita" | `agendar` | `agendar_visita()` |
| "quantos corretores têm?" | `corretores` | `info_corretores()` |

---

## 🌐 Deploy em Produção

### Backend → Railway

```bash
# O Procfile já configura tudo automaticamente
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

Variáveis de ambiente no Railway:
```
DATABASE_URL = sua_string_do_neon
```

### Frontend → Vercel

O `vercel.json` garante que apenas o HTML seja servido:

```json
{
  "version": 2,
  "builds": [{ "src": "web/index.html", "use": "@vercel/static" }],
  "routes": [{ "src": "/(.*)", "dest": "web/$1" }]
}
```

### Atualizar em produção

```bash
git add .
git commit -m "sua alteração"
git push
# Railway e Vercel atualizam automaticamente ✅
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Motivo |
|---|---|---|
| Frontend | HTML + CSS + JS vanilla | Leve, rápido, sem dependências |
| Backend | Python + FastAPI | Alta performance, fácil manutenção |
| Banco | PostgreSQL (Neon) | Confiável, escalável, gratuito |
| Hospedagem API | Railway | Deploy automático via GitHub |
| Hospedagem UI | Vercel | CDN global, HTTPS automático |
| Versionamento | GitHub | Colaboração e CI/CD |

---

## 📞 Contato e Suporte

<div align="center">

**ImobiliáriaPerto**  
Assistente desenvolvido por **STR Software**

🌐 [www.strsoftware.com.br](https://www.strsoftware.com.br)  
💬 WhatsApp: [(11) 97666-1297](https://wa.me/5511976661297)

---

*Feito com ❤️ por STR Software — Tecnologia a serviço do mercado imobiliário*

</div>
