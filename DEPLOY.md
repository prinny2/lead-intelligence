# Deploy na web

Os dados continuam em **arquivo JSONL** (`leads.jsonl`), salvo onde você apontar com `LEADS_FILE`. Na nuvem, o disco do container costuma ser **efêmero**: ao redeploy, o arquivo some, a menos que use **disco persistente** ou um banco depois.

## Variáveis de ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | Sim (para IA no `/lead`) | Chave da OpenAI |
| `PORT` | Não | Injetado por Render/Railway/Fly |
| `LEADS_FILE` | Não | Caminho absoluto do JSONL (ex.: `/data/leads.jsonl` com disco persistente) |
| `CORS_ORIGINS` | Não | Origens separadas por vírgula, ou `*` para qualquer origem (só teste/MVP) |

Copie `env.example` para `.env` localmente.

---

## Opção A — Render.com

1. Crie conta em [render.com](https://render.com).
2. **New → Blueprint** e conecte o repositório GitHub (ou **Web Service** manual).
3. Se usar o `render.yaml`, o build/start já vêm definidos.
4. No painel do serviço → **Environment**:
   - Adicione `OPENAI_API_KEY` (secret).
   - Opcional: `CORS_ORIGINS=https://seu-frontend.com`
5. **Disco persistente (recomendado para não perder leads):**
   - **Settings → Disks** → monte um disco em `/data`
   - Defina `LEADS_FILE=/data/leads.jsonl`
6. URL pública: `https://lead-intelligence-api.onrender.com` (exemplo).  
   - Docs: `https://....onrender.com/docs`

---

## Opção B — Railway.app

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub.
2. Variáveis: `OPENAI_API_KEY`, opcional `CORS_ORIGINS`, `LEADS_FILE`.
3. Railway define `PORT` automaticamente. O `Procfile` funciona se o build detectar Python.

*Nota:* sem volume persistente, `leads.jsonl` reinicia vazio a cada deploy.

---

## Opção C — Docker (Fly.io, ECS, etc.)

```bash
docker build -t lead-intelligence .
docker run -e OPENAI_API_KEY=sk-... -e PORT=8000 -p 8000:8000 lead-intelligence
```

Monte um volume no caminho de `LEADS_FILE` se quiser persistência.

---

## Testar depois do deploy

```bash
curl -s https://SUA-URL/health
curl -s https://SUA-URL/docs
```

---

## Próximo passo (dados “de verdade” na web)

- **PostgreSQL** (Render/Railway/Supabase) + trocar `storage_service` para gravar no DB, ou  
- **S3 / R2** para append de JSONL, ou  
- Disco persistente + backup do `leads.jsonl`.

Quer evoluir para Postgres depois, dá para fazer em etapa pequena sem quebrar a API.
