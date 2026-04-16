#!/bin/bash
# =============================================================
# LeadSolar — Setup inicial Cloud Run (roda uma vez)
# Projeto: lead-solar-12345 | Região: southamerica-east1
# =============================================================
set -e

PROJECT_ID="lead-solar-12345"
REGION="southamerica-east1"
REPO="leadsolar"
SERVICE="leadsolar-api"

echo "🚀 Configurando Cloud Run para LeadSolar..."

# 1. Configurar projeto e região
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# 2. Habilitar APIs necessárias
echo "📡 Habilitando APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --quiet

# 3. Criar Artifact Registry
echo "📦 Criando Artifact Registry..."
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="LeadSolar API images" \
  --quiet 2>/dev/null || echo "✓ Registry já existe"

# 4. Configurar Docker para Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# 5. Migrar variáveis do Railway para Secret Manager
echo "🔐 Criando secrets no Secret Manager..."
echo "⚠️  Cole o valor de cada secret quando solicitado (copie do Railway)."
echo ""

SECRETS=(
  "ANTHROPIC_API_KEY"
  "GEMINI_API_KEY"
  "GOOGLE_APPLICATION_CREDENTIALS_JSON"
  "GOOGLE_CLOUD_PROJECT"
  "FIREBASE_AUTH_DOMAIN"
  "FIREBASE_WEB_API_KEY"
  "STRIPE_SECRET_KEY"
  "STRIPE_WEBHOOK_SECRET"
  "RESEND_API_KEY"
  "NOTIFY_FROM_EMAIL"
  "NOTIFY_ADMIN_EMAIL"
  "GOOGLE_MAPS_API_KEY"
  "SENTRY_DSN"
  "REDIS_URL"
  "BASE_URL"
)

for SECRET in "${SECRETS[@]}"; do
  echo -n "  → $SECRET: "
  read -s SECRET_VALUE
  echo ""
  echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET \
    --data-file=- \
    --replication-policy=automatic \
    --quiet 2>/dev/null || \
  echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET --data-file=- --quiet
  echo "  ✓ $SECRET salvo"
done

# 6. Dar permissão ao Cloud Build para acessar secrets
echo "🔑 Configurando permissões..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CB_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
CR_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/run.admin" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/iam.serviceAccountUser" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CR_SA" \
  --role="roles/secretmanager.secretAccessor" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CB_SA" \
  --role="roles/secretmanager.secretAccessor" --quiet

# 7. Conectar GitHub ao Cloud Build
echo ""
echo "✅ Infraestrutura pronta!"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "   1. Acesse: https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo "   2. Clique em 'Conectar repositório' → GitHub → prinny2/lead-intelligence"
echo "   3. Crie um trigger: Push na branch main → cloudbuild.yaml"
echo "   4. Primeiro deploy manual: gcloud builds submit --config cloudbuild.yaml ."
echo ""
echo "   Após o deploy, atualize o DNS no Cloudflare:"
echo "   CNAME leadsolarintelligence.com.br → [URL do Cloud Run]"
