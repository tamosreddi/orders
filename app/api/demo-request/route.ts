import { NextResponse } from 'next/server';
import { Resend } from 'resend';

export async function POST(request: Request) {
  try {
    const { email } = await request.json();

    if (!email) {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 });
    }

    // Store in Supabase
    const supabaseUrl = process.env.SUPABASE_PROJECT_URL!;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

    const response = await fetch(`${supabaseUrl}/rest/v1/demo_requests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
      },
      body: JSON.stringify({
        email,
        created_at: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      console.error('Failed to store demo request');
    }

    // Send email notification using Resend
    if (process.env.RESEND_API_KEY) {
      const resend = new Resend(process.env.RESEND_API_KEY);
      
      try {
        await resend.emails.send({
          from: 'Reddi AI <onboarding@resend.dev>', // Use this for testing, change to your domain later
          to: 'tamosreddi@gmail.com',
          subject: 'New Demo Request - Reddi AI',
          html: `
            <h2>New Demo Request</h2>
            <p>You have received a new demo request from:</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
            <hr>
            <p><small>This email was sent from your Reddi AI website.</small></p>
          `,
        });
      } catch (emailError) {
        console.error('Failed to send email notification:', emailError);
        // Don't fail the request if email fails - data is still saved in Supabase
      }
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error processing demo request:', error);
    return NextResponse.json({ error: 'Failed to process request' }, { status: 500 });
  }
}