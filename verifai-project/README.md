# VerifAI – Sistema de Auditoria Digital

> MVP de detecção de desinformação com 3 camadas de verificação.  
> Stack: **FastAPI + Gemini 1.5 Flash (grátis) + Google Fact Check API (grátis) + React + Vite**

---

## 🚀 Como rodar em 5 minutos

### Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e rodando
- Chaves de API gratuitas (veja abaixo)

---

## 🔑 APIs gratuitas necessárias

### 1. Google Gemini (IA principal)
1. Acesse: https://aistudio.google.com/app/apikey
2. Clique em **"Create API Key"**
3. Copie a chave (começa com `AIza...`)

### 2. Google Fact Check Explorer (opcional, melhora resultados)
1. Acesse: https://console.cloud.google.com
2. Crie um projeto (ou use um existente)
3. Vá em **APIs & Services → Library**
4. Busque "Fact Check Tools API" e **ative**
5. Vá em **APIs & Services → Credentials → Create Credentials → API Key**
6. Copie a chave

---

## ⚙️ Configuração

1. **Clone / baixe o projeto**

2. **Configure as chaves** no arquivo `backend/.env`:
```
GEMINI_API_KEY=sua_chave_gemini_aqui
GOOGLE_FACT_CHECK_KEY=sua_chave_fact_check_aqui
```

3. **Suba tudo com um comando:**
```bash
docker-compose up --build
```

4. **Acesse:**
- Frontend: http://localhost:5173
- Backend (docs Swagger): http://localhost:8000/docs

---

## 🏗️ Estrutura do Projeto

```
verifai-project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── check_text.py   # POST /api/check-text
│   │   │   ├── check_url.py    # POST /api/check-url
│   │   │   └── upload.py       # POST /api/upload (imagens)
│   │   ├── core/
│   │   │   ├── pipeline.py         # Orquestrador das 3 camadas
│   │   │   ├── gemini_analyzer.py  # Camada 3: IA semântica
│   │   │   ├── fact_checker.py     # Camada 1: Google Fact Check
│   │   │   └── domain_checker.py   # Camada 2: Reputação de domínio
│   │   ├── models/
│   │   │   └── schemas.py      # Modelos Pydantic
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                    # ← SUAS CHAVES AQUI
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── GaugeChart.jsx
│   │   │   ├── MetricBar.jsx
│   │   │   ├── Dropzone.jsx
│   │   │   └── LoadingScreen.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx        # Input (texto/URL/imagem)
│   │   │   ├── ReportPage.jsx  # Resultado detalhado
│   │   │   └── Dashboard.jsx   # Histórico de análises
│   │   ├── services/
│   │   │   └── api.js          # Axios → backend
│   │   └── App.jsx
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## 🔬 Pipeline de Verificação

```
Input (texto / URL / imagem)
         │
         ▼
┌─────────────────────────────┐
│ CAMADA 1 – Fact Check       │  Google Fact Check Explorer API
│ Busca checagens existentes  │  (gratuita)
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ CAMADA 2 – Domínio          │  Heurística local
│ Reputação da fonte/URL      │  (sem API, 0 custo)
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ CAMADA 3 – IA Semântica     │  Gemini 1.5 Flash
│ NLP, falácias, sensac.      │  (gratuito até 15 req/min)
└──────────────┬──────────────┘
               │
               ▼
        Score 0–100
     Laudo explicável
```

---

## 🛠️ Desenvolvimento local (sem Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

---

## 📋 Endpoints da API

| Método | Rota              | Descrição                         |
|--------|-------------------|-----------------------------------|
| POST   | `/api/check-text` | Analisa texto bruto               |
| POST   | `/api/check-url`  | Scraping + análise de URL         |
| POST   | `/api/upload`     | Análise de imagem (Gemini Vision) |
| GET    | `/health`         | Health check                      |
| GET    | `/docs`           | Swagger UI                        |

---

## 💡 Próximos passos (pós-MVP)

- [ ] Persistência com PostgreSQL
- [ ] Autenticação (JWT)
- [ ] Exportar relatório em PDF
- [ ] Análise de vídeo (Gemini 1.5 Pro)
- [ ] Dashboard com gráficos históricos reais
- [ ] Cache Redis para queries repetidas
