# Resend Email Setup

## Steps to Complete Setup:

### 1. Sign up for Resend
1. Go to [resend.com](https://resend.com)
2. Sign up for a free account (100 emails/day free)

### 2. Get your API Key
1. After signing up, go to API Keys section
2. Create a new API key
3. Copy the key (starts with `re_`)

### 3. Add to Environment Variables

#### For Local Development:
Add to your `.env` file:
```
RESEND_API_KEY=re_your_api_key_here
```

#### For Vercel:
1. Go to your Vercel project settings
2. Navigate to Environment Variables
3. Add `RESEND_API_KEY` with your key

### 4. Email Domain Setup (Optional)

For now, emails will come from `onboarding@resend.dev` (Resend's test domain).

To use your own domain later:
1. Add reddi.ai domain in Resend dashboard
2. Verify DNS records
3. Update the `from` email in the code to `noreply@reddi.ai`

## Testing

1. Run your app locally: `npm run dev`
2. Submit an email in the form
3. Check:
   - Supabase dashboard for the stored record
   - Your email at tamosreddi@gmail.com for the notification

## What Happens When Someone Submits:

1. Email is stored in Supabase `demo_requests` table
2. Email notification sent to tamosreddi@gmail.com
3. User sees success message
4. If email fails, data is still saved (no lost leads!)

## Viewing All Demo Requests

Go to Supabase Dashboard > Table Editor > demo_requests to see all submissions.