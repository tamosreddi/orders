import { NextRequest, NextResponse } from 'next/server';

/**
 * Minimal Twilio WhatsApp webhook that works
 * Just forwards to AI agent without complex validation
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  console.log('🔔 Simple Twilio webhook received');

  try {
    // Parse form data from Twilio
    const formData = await request.formData();
    const payload: Record<string, any> = {};
    
    formData.forEach((value, key) => {
      payload[key] = value.toString();
    });

    console.log('📝 Webhook payload:', {
      From: payload.From,
      To: payload.To,
      Body: payload.Body,
      MessageSid: payload.MessageSid
    });

    // Extract phone number (remove whatsapp: prefix)
    const phoneNumber = payload.From?.replace('whatsapp:', '') || '';
    const messageBody = payload.Body || '';

    // Forward to AI agent if enabled
    if (process.env.USE_AI_AGENT_WEBHOOK === 'true') {
      try {
        const aiAgentUrl = process.env.AI_AGENT_URL || 'http://localhost:8001';
        
        const aiResponse = await fetch(`${aiAgentUrl}/process-message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_id: payload.MessageSid,
            customer_id: phoneNumber,
            conversation_id: `conv_${phoneNumber.replace('+', '')}`,
            content: messageBody,
            channel: 'WHATSAPP'
          })
        });

        console.log('🤖 AI agent response status:', aiResponse.status);
      } catch (aiError) {
        console.error('⚠️ AI agent failed:', aiError);
      }
    }

    // Return empty TwiML (no auto-response)
    const twimlResponse = `<?xml version="1.0" encoding="UTF-8"?><Response></Response>`;
    
    return new NextResponse(twimlResponse, {
      status: 200,
      headers: { 'Content-Type': 'text/xml' }
    });

  } catch (error) {
    console.error('💥 Simple webhook error:', error);
    
    // Return empty TwiML even on error
    const twimlResponse = `<?xml version="1.0" encoding="UTF-8"?><Response></Response>`;
    return new NextResponse(twimlResponse, {
      status: 200,
      headers: { 'Content-Type': 'text/xml' }
    });
  }
}