#!/bin/bash
# Deploy LeadSolar to Google Cloud Run
# Usage: bash deploy-cloudrun.sh YOUR_PROJECT_ID YOUR_ANTHROPIC_KEY YOUR_API_KEY

set -e

PROJECT_ID="${1:-leadsolar}"
ANTHROPIC_KEY="${2:-}"
API_KEY="${3:-minha-chave-secreta}"
REGION="us-central1"
SERVICE="leadsolar"

echo "=== LeadSolar → Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  --project "$PROJECT_ID"

# Create Firestore database (native mode) if not exists
echo "Setting up Firestore..."
gcloud firestore databases create --location=us-central --project "$PROJECT_ID" 2>/dev/null || true

# Deploy to Cloud Run (builds from Dockerfile automatically)
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "ANTHROPIC_API_KEY=${ANTHROPIC_KEY},API_KEY=${API_KEY},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --project "$PROJECT_ID"

echo ""
echo "=== Deploy concluído! ==="
SERVICE_URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format "value(status.url)")
echo "URL: $SERVICE_URL"
echo "Landing: $SERVICE_URL/"
echo "Dashboard: $SERVICE_URL/dashboard"
echo "API docs: $SERVICE_URL/docs"
