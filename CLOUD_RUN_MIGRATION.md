# Migrar Railway → Google Cloud Run

## Por que migrar?

- Firebase Auth, Firestore, Gemini, Maps Solar API — tudo Google
- Billing unificado no GCP
- Secret Manager (mais seguro que Railway vars)
- Cloud Build + GitHub trigger (CI/CD nativo)
- Free tier: 2M requests/mês, 360k GB-seconds
- CDN global via Firebase Hosting (para static files)
- Logs centralizados no Cloud Logging + Error Reporting

## Pre-requisitos

- GCP project com billing ativo
- `gcloud` CLI instalado
- Domínio `leadsolarinteligence.com.br` configurado

## Passo a passo

### 1. Habilitar APIs necessárias

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  compute.googleapis.com
```

### 2. Criar secrets no Secret Manager

```bash
# Para cada secret:
echo -n "sk_live_..." | gcloud secrets create STRIPE_SECRET_KEY --data-file=-
echo -n "whsec_..." | gcloud secrets create STRIPE_WEBHOOK_SECRET --data-file=-
echo -n "..." | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "..." | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
echo -n "re_..." | gcloud secrets create RESEND_API_KEY --data-file=-
echo -n '{"type":"service_account",...}' | gcloud secrets create GOOGLE_APPLICATION_CREDENTIALS_JSON --data-file=-
echo -n "..." | gcloud secrets create FIREBASE_WEB_API_KEY --data-file=-
```

### 3. Dar permissão ao Cloud Run

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding STRIPE_SECRET_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Repetir para cada secret...
```

### 4. Conectar GitHub ao Cloud Build

```bash
# Via Console: Cloud Build → Triggers → Connect Repository → GitHub
# Ou CLI:
gcloud builds triggers create github \
  --repo-name=lead-intelligence \
  --repo-owner=prinny2 \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml
```

### 5. Deploy manual (primeira vez)

```bash
gcloud builds submit --config=cloudbuild.yaml
```

### 6. Mapear domínio

```bash
gcloud run domain-mappings create \
  --service=lead-intelligence \
  --domain=leadsolarinteligence.com.br \
  --region=southamerica-east1
```

O comando retorna registros DNS (A e/ou AAAA) para configurar no registrar.

### 7. Configurar Stripe webhook

No Stripe Dashboard:
- URL: `https://leadsolarinteligence.com.br/webhook/stripe`
- Eventos: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`, `invoice.paid`
- Copiar `whsec_...` e atualizar no Secret Manager

### 8. Desligar Railway

Após confirmar que Cloud Run está rodando:
1. Railway → project → Settings → Delete project
2. Remover `railway.json`, `nixpacks.toml`, `Procfile` do repo

## Custos estimados

| Recurso | Estimativa/mês |
|---------|---------------|
| Cloud Run (min-instances=1, 512Mi) | ~$5-15 |
| Firestore (10k reads/day) | $0 (free tier) |
| Secret Manager (6 secrets) | $0 (free tier) |
| Cloud Build (120 min/mês) | $0 (free tier) |
| **Total** | **~$5-15/mês** |

vs Railway: ~$5/mês (Hobby) + Redis add-on

## Redis

Para rate limiting no Cloud Run, opções:
1. **Memorystore Redis** — managed, ~$30/mês (overkill)
2. **Upstash Redis** — serverless, free tier 10k cmd/dia
3. **Firestore fallback** — já implementado no código, ~50ms latência

Recomendação: usar Firestore fallback inicialmente, migrar para Upstash se precisar de performance.
