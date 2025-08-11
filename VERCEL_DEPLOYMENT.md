# Vercel Deployment Guide for ReddiAI

## Prerequisites
- GitHub repository connected (already done)
- Vercel account
- Domain reddiAI.com configured

## Steps to Deploy

### 1. Connect to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository: `tamosreddi/orders`
4. Configure project settings

### 2. Environment Variables
Add these in Vercel dashboard under Settings > Environment Variables:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_PROJECT_URL=https://ckapulfmocievprlnzux.supabase.co
SUPABASE_API_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
NEXT_PUBLIC_SUPABASE_URL=https://ckapulfmocievprlnzux.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Build Settings
- Framework Preset: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

### 4. Domain Configuration
1. Go to Settings > Domains
2. Add `reddiAI.com` and `www.reddiAI.com`
3. Follow Vercel's DNS configuration instructions

### 5. Authentication Setup
The app is configured to:
- Show landing page at `/` (public)
- Protect `/orders`, `/customers`, `/products`, `/messages`
- Redirect to login when accessing protected routes

### 6. Deploy
1. Push code to GitHub
2. Vercel will automatically deploy
3. Check deployment at your-project.vercel.app first
4. Then verify at reddiAI.com

## Post-Deployment

### Configure Supabase Auth
1. Go to Supabase Dashboard > Authentication > URL Configuration
2. Add these to "Redirect URLs":
   - `https://reddiAI.com/auth/callback`
   - `https://www.reddiAI.com/auth/callback`
   - `http://localhost:3000/auth/callback` (for local dev)

### Enable OAuth Providers (if using)
1. Go to Authentication > Providers
2. Enable Google OAuth (or others)
3. Add client ID and secret
4. Save configuration