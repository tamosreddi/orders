# Email Notification Setup for Demo Requests

## Option 1: Using Resend (Recommended - Easiest)

1. Sign up at [resend.com](https://resend.com)
2. Get your API key
3. Install: `npm install resend`
4. Add to `.env`: `RESEND_API_KEY=your_key`
5. Uncomment the Resend code in `/app/api/demo-request/route.ts`

## Option 2: Using SendGrid

1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Get your API key
3. Install: `npm install @sendgrid/mail`
4. Add to `.env`: `SENDGRID_API_KEY=your_key`
5. Uncomment the SendGrid code in `/app/api/demo-request/route.ts`

## Option 3: Using Supabase Edge Functions (Free)

Create an Edge Function that sends emails when new rows are added to demo_requests table.

## Option 4: Quick Solution - Webhook to Zapier/Make

1. Create a Zapier/Make webhook
2. Update the API route to send data to the webhook
3. Configure Zapier/Make to send email to tamosreddi@gmail.com

## Current Setup

Right now, demo requests are:
1. Stored in Supabase `demo_requests` table
2. Logged to console (visible in Vercel logs)

To view demo requests immediately:
- Go to Supabase Dashboard > Table Editor > demo_requests
- Or create a simple admin page to view them