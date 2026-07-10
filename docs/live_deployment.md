# Live Production Hosting & Deployment Guide

This guide details the step-by-step process to host your FastAPI backend and Next.js frontend live on the web for free.

---

## 🗄️ Step 1: Verify Supabase Database
Your database schema has already been fully updated. The `disaster_data` and `updated_at` columns are applied to your live Supabase database. No action is required here!

---

## 🐍 Step 2: Host the FastAPI Backend (on Render)
We recommend **Render** because it offers a free container hosting tier, connects directly to your GitHub, and reads the `backend/Dockerfile` to build automatically.

1.  **Sign Up / Sign In:** Go to [Render Dashboard](https://dashboard.render.com/) and log in with your GitHub account.
2.  **Create Service:** Click the **New** button (top right) and select **Web Service**.
3.  **Connect Repo:** Select your repository `project` (or paste `https://github.com/allanmaaz/project.git`).
4.  **Configure settings:**
    *   **Name:** `clarify-ai-backend`
    *   **Region:** Select the region closest to you (e.g., Singapore/Oregon).
    *   **Branch:** `main`
    *   **Root Directory:** `backend`
    *   **Runtime:** `Docker` (Render will automatically detect the `Dockerfile` inside `backend/`).
    *   **Instance Type:** `Free`
5.  **Configure Environment Variables (under Advanced):**
    Click **Add Environment Variable** and copy-paste these values from your local configuration:
    *   `APP_ENV`: `production`
    *   `DATABASE_URL`: `postgresql+asyncpg://postgres.zzwspcijmoeoxsdpciiv:Project%40100%251234@aws-1-ap-south-1.pooler.supabase.com:5432/postgres` *(pooled connection string)*
    *   `SUPABASE_URL`: `https://zzwspcijmoeoxsdpciiv.supabase.co`
    *   `SUPABASE_ANON_KEY`: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6d3NwY2lqbW9lb3hzZHBjaWl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2MTc1OTAsImV4cCI6MjA5OTE5MzU5MH0.MKR1VwHPpA0y7fE0S6372lDVSOusY7XIPoPDP0d1HrU`
    *   `SUPABASE_SERVICE_KEY`: *(Your Supabase service role key for admin tasks)*
    *   `SUPABASE_JWT_SECRET`: `Project@100%1234`
    *   `GEMINI_API_KEY`: *(Your Google Gemini API key)*
6.  **Deploy:** Click **Create Web Service**. Render will build and deploy your container. Once completed, it will provide you with a live URL (e.g., `https://clarify-ai-backend.onrender.com`).

---

## ⚛️ Step 3: Host the Next.js Frontend (on Vercel)
Vercel is the creators of Next.js and hosts your frontend with global CDNs and automatic builds.

1.  **Sign Up / Sign In:** Go to [Vercel](https://vercel.com/) and log in with GitHub.
2.  **Add New Project:** Click **Add New** -> **Project**.
3.  **Import Repo:** Choose your repository `project`.
4.  **Configure settings:**
    *   **Project Name:** `clarify-ai`
    *   **Framework Preset:** `Next.js`
    *   **Root Directory:** Click **Edit** and select `frontend`.
5.  **Configure Environment Variables:**
    Expand the **Environment Variables** section and add:
    *   `NEXT_PUBLIC_SUPABASE_URL`: `https://zzwspcijmoeoxsdpciiv.supabase.co`
    *   `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6d3NwY2lqbW9lb3hzZHBjaWl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM2MTc1OTAsImV4cCI6MjA5OTE5MzU5MH0.MKR1VwHPpA0y7fE0S6372lDVSOusY7XIPoPDP0d1HrU`
    *   `NEXT_PUBLIC_API_URL`: *(Paste your live Render backend URL from Step 2, e.g. `https://clarify-ai-backend.onrender.com`)*
6.  **Deploy:** Click **Deploy**. Vercel will build your Next.js app and give you a live domain (e.g., `https://clarify-ai.vercel.app`)!

---

## ⚙️ Step 4: Configure Supabase Auth Redirects
Because you are now hosting the site live, you must tell Supabase to allow login redirects to your new live domain!

1.  Go to the [Supabase Dashboard](https://database.supabase.com/) for your project.
2.  Navigate to **Authentication** -> **URL Configuration**.
3.  Set the **Site URL** to your live Vercel frontend domain: `https://clarify-ai.vercel.app`.
4.  Under **Redirect URLs**, add: `https://clarify-ai.vercel.app/**`.
5.  Save changes.
