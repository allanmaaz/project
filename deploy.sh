#!/bin/bash

# Clarify AI - Live Production Deployment Script
# This script automates build validation, Supabase schema migration, and deploying frontend/backend.

set -e

# Styling colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "=========================================================="
echo "    🚀 CLARIFY AI - PRODUCTION DEPLOYMENT ENGINE 🚀       "
echo "=========================================================="
echo -e "${NC}"

# Check dependencies
echo -e "${BLUE}[1/4] Checking local CLI dependencies...${NC}"
HAS_SUPABASE=false
HAS_VERCEL=false
HAS_GCLOUD=false

if command -v supabase &> /dev/null; then
    HAS_SUPABASE=true
    echo -e "  ${GREEN}✓${NC} Supabase CLI detected"
else
    echo -e "  ${YELLOW}!${NC} Supabase CLI not installed. (Optional: useful for automated DB migrations)"
fi

if command -v vercel &> /dev/null; then
    HAS_VERCEL=true
    echo -e "  ${GREEN}✓${NC} Vercel CLI detected"
else
    echo -e "  ${YELLOW}!${NC} Vercel CLI not installed. (Will deploy frontend manually)"
fi

if command -v gcloud &> /dev/null; then
    HAS_GCLOUD=true
    echo -e "  ${GREEN}✓${NC} Google Cloud CLI detected"
else
    echo -e "  ${YELLOW}!${NC} Google Cloud CLI not installed."
fi

# Step 2: Database schema check/apply
echo -e "\n${BLUE}[2/4] Syncing database migrations...${NC}"
if [ "$HAS_SUPABASE" = true ]; then
    read -p "Do you want to push migrations to your live Supabase DB? (y/n): " confirm_db
    if [ "$confirm_db" = "y" ] || [ "$confirm_db" = "Y" ]; then
        echo -e "${YELLOW}Applying migrations to live database...${NC}"
        supabase db push
        echo -e "${GREEN}✓ Migrations pushed successfully!${NC}"
    else
        echo "Skipping automated database migrations."
    fi
else
    echo -e "${YELLOW}Notice:${NC} Please ensure your Supabase database schema is up-to-date by running the SQL scripts in './supabase/migrations/' directly in your Supabase SQL Editor."
fi

# Step 3: Deploy FastAPI Backend
echo -e "\n${BLUE}[3/4] Deploying FastAPI Backend...${NC}"
echo "Select your backend hosting provider:"
echo "  1) Google Cloud Run (Recommended, fast, free tier)"
echo "  2) Render (Simple setup, free tier)"
echo "  3) Railway (Simple, paid tier)"
echo "  4) Skip backend deployment"
read -p "Enter choice (1-4): " backend_choice

case $backend_choice in
    1)
        echo -e "\n${YELLOW}Deploying backend to Google Cloud Run...${NC}"
        if [ "$HAS_GCLOUD" = true ]; then
            read -p "Enter your Google Cloud Project ID: " gcp_project
            read -p "Enter preferred region (e.g., us-central1, asia-south1): " gcp_region
            gcloud config set project "$gcp_project"
            gcloud builds submit --tag gcr.io/"$gcp_project"/clarify-backend ./backend
            gcloud run deploy clarify-backend \
                --image gcr.io/"$gcp_project"/clarify-backend \
                --platform managed \
                --region "$gcp_region" \
                --allow-unauthenticated
            echo -e "${GREEN}✓ Backend deployed successfully to Google Cloud Run!${NC}"
        else
            echo -e "${RED}Error:${NC} gcloud CLI not found. Please install the Google Cloud SDK or deploy via your Github repository connection on Cloud Run."
        fi
        ;;
    2)
        echo -e "\n${YELLOW}Deploying backend to Render:${NC}"
        echo "1. Sign in to https://dashboard.render.com"
        echo "2. Click 'New' -> 'Web Service'"
        echo "3. Connect your GitHub repository: 'https://github.com/allanmaaz/project.git'"
        echo "4. Set the following options:"
        echo "   - Root Directory: 'backend'"
        echo "   - Runtime: 'Docker'"
        echo "5. Add Environment Variables (Advanced):"
        echo "   - DATABASE_URL: (Your pooled Supabase Connection string)"
        echo "   - SUPABASE_URL: (Your Supabase project URL)"
        echo "   - SUPABASE_SERVICE_KEY: (Your Supabase Service role key)"
        echo "   - SUPABASE_JWT_SECRET: (Your Supabase JWT Secret)"
        echo "   - GEMINI_API_KEY: (Your Google Gemini API Key)"
        ;;
    3)
        echo -e "\n${YELLOW}Deploying backend to Railway:${NC}"
        echo "1. Go to https://railway.app"
        echo "2. Create a new Project -> Deploy from GitHub"
        echo "3. Select your repository: 'https://github.com/allanmaaz/project.git'"
        echo "4. In settings, set the 'Root Directory' to 'backend'."
        echo "5. Add the same Environment Variables as Render above."
        ;;
    *)
        echo "Skipping backend deployment."
        ;;
esac

# Step 4: Deploy Next.js Frontend
echo -e "\n${BLUE}[4/4] Deploying Next.js Frontend...${NC}"
if [ "$HAS_VERCEL" = true ]; then
    read -p "Do you want to deploy the frontend to Vercel now? (y/n): " confirm_frontend
    if [ "$confirm_frontend" = "y" ] || [ "$confirm_frontend" = "Y" ]; then
        cd frontend
        vercel --prod
        cd ..
        echo -e "${GREEN}✓ Frontend deployed to Vercel!${NC}"
    else
        echo "Skipping automated frontend deployment."
    fi
else
    echo -e "${YELLOW}To deploy your Frontend to Vercel manually:${NC}"
    echo "1. Import your GitHub repository into Vercel (https://vercel.com)."
    echo "2. In the configuration page, set 'Root Directory' to 'frontend'."
    echo "3. Set the following Environment Variables:"
    echo "   - NEXT_PUBLIC_SUPABASE_URL: (Your Supabase project URL)"
    echo "   - NEXT_PUBLIC_SUPABASE_ANON_KEY: (Your Supabase Anon key)"
    echo "   - NEXT_PUBLIC_API_URL: (Your live FastAPI backend URL, e.g., https://backend-xxx.run.app)"
    echo -e "\n${GREEN}✓ Setup complete! Your website is ready for deployment.${NC}"
fi

echo -e "\n${GREEN}🎉 Deployment process initialized/documented successfully! 🎉${NC}\n"
