import { NextRequest, NextResponse } from 'next/server';
import { 
  validateTwilioSignature, 
  validateWebhookPayload,
  formatTwiMLResponse,
  getDefaultDistributorId,
  validateEnvironmentVariables,
  WHATSAPP_RESPONSES
} from '../../../../lib/utils/twilio';
import { processWhatsAppMessage } from '../../../../lib/api/whatsapp';
import { 
  WhatsAppError, 
  WHATSAPP_ERROR_MESSAGES,
  TwilioWebhookPayload 
} from '../../../../types/twilio';

/**
 * POST handler for Twilio WhatsApp webhook
 * Receives incoming WhatsApp messages and processes them
 * CRITICAL: Next.js 14 App Router pattern - export async function POST(request: Request)
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  console.log('🔔 Twilio webhook received');

  try {
    // Validate environment variables first
    validateEnvironmentVariables();

    // CRITICAL: Parse form data (Twilio sends application/x-www-form-urlencoded)
    const formData = await request.formData();
    const payload: Record<string, any> = {};
    
    // Convert FormData to plain object for processing
    formData.forEach((value, key) => {
      payload[key] = value.toString();
    });

    console.log('📝 Webhook payload received:', {
      From: payload.From,
      To: payload.To,
      Body: payload.Body?.substring(0, 100) + '...', // Log first 100 chars only
      MessageSid: payload.MessageSid,
      NumMedia: payload.NumMedia
    });

    // CRITICAL: Validate Twilio signature for security
    // Skip signature validation in test mode
    const skipValidation = process.env.TWILIO_SKIP_SIGNATURE_VALIDATION === 'true';
    
    const signature = request.headers.get('x-twilio-signature');
    if (!signature && !skipValidation) {
      console.error('❌ Missing Twilio signature header');
      return new NextResponse('Missing signature', { status: 401 });
    }

    // Only do signature validation if not in test mode
    let isSignatureValid = true;
    
    if (!skipValidation) {
      // Construct the exact URL Twilio used to send the webhook
      const url = process.env.NEXT_PUBLIC_WEBHOOK_URL;
      if (!url) {
        console.error('❌ Missing webhook URL configuration');
        return new NextResponse('Configuration error', { status: 500 });
      }

      const authToken = process.env.TWILIO_AUTH_TOKEN;
      if (!authToken) {
        console.error('❌ Missing TWILIO_AUTH_TOKEN configuration');
        return new NextResponse('Configuration error', { status: 500 });
      }

      isSignatureValid = validateTwilioSignature(
        authToken,
        signature!,
        url,
        payload
      );

      if (!isSignatureValid) {
        console.error('❌ Twilio signature validation failed');
        return new NextResponse('Unauthorized', { status: 401 });
      }
      
      console.log('✅ Twilio signature validated');
    } else {
      console.log('🧪 Signature validation skipped (test mode)');
    }

    // Validate webhook payload structure
    const validationResult = validateWebhookPayload(payload);
    if (!validationResult.isValid) {
      console.error('❌ Invalid webhook payload:', validationResult.error);
      
      // Return empty TwiML response (no message sent to user)
      const errorResponse = formatTwiMLResponse();
      return new NextResponse(errorResponse, {
        status: 200, // Return 200 to prevent Twilio retries for invalid payloads
        headers: { 'Content-Type': 'text/xml' }
      });
    }

    const validatedPayload = validationResult.payload as TwilioWebhookPayload;
    console.log('✅ Payload validated');

    // GOTCHA: Default to demo distributor for sandbox testing
    const distributorId = getDefaultDistributorId();
    console.log(`🏢 Using distributor ID: ${distributorId}`);

    // Process the WhatsApp message
    // SEQUENCE: Customer -> Conversation -> Message (no transactions available)
    console.log('🔄 Processing WhatsApp message...');
    const result = await processWhatsAppMessage(validatedPayload, distributorId);
    
    console.log('✅ Message processed successfully:', {
      customerId: result.customer.id,
      conversationId: result.conversation.id,
      messageId: result.message.id
    });

    // INTEGRATION: Trigger AI agent processing in the background
    // DISABLED: AI processing is already triggered in processWhatsAppMessage to avoid duplicate orders
    // try {
    //   await triggerAIAgentProcessing({
    //     messageId: result.message.id,
    //     customerId: result.customer.id,
    //     conversationId: result.conversation.id,
    //     content: validatedPayload.Body,
    //     distributorId: distributorId,
    //     channel: 'WHATSAPP'
    //   });
    //   console.log('🤖 AI agent processing triggered successfully');
    // } catch (aiError) {
    //   // Log but don't fail the webhook - message is already stored
    //   console.error('⚠️ Failed to trigger AI agent processing:', aiError);
    //   // AI processing will be picked up by polling loop as fallback
    // }

    // Real-time updates are handled automatically by Supabase Realtime
    console.log('✅ Message processed - real-time updates via Supabase Realtime');

    // CRITICAL: Return empty TwiML XML response (Twilio requirement)
    // No automatic message will be sent to the user
    const twimlResponse = formatTwiMLResponse();
    
    console.log('📤 Sending TwiML response');
    return new NextResponse(twimlResponse, {
      status: 200,
      headers: { 'Content-Type': 'text/xml' }
    });

  } catch (error) {
    console.error('💥 Webhook processing error:', error);

    // Handle specific WhatsApp errors
    if (error instanceof WhatsAppError) {
      console.error(`WhatsApp Error [${error.code}]:`, error.message);
      
      // Log the original error for debugging but don't expose to Twilio
      if (error.originalError) {
        console.error('Original error:', error.originalError);
      }
      
      // Return empty TwiML response (no error message sent to user)
      const errorResponse = formatTwiMLResponse();
      return new NextResponse(errorResponse, {
        status: 200, // Return 200 to prevent Twilio retries for application errors
        headers: { 'Content-Type': 'text/xml' }
      });
    }

    // Handle unexpected errors
    console.error('Unexpected error in webhook processing:', error);
    
    // PATTERN: Log error but return empty TwiML (no message sent to user)
    const errorResponse = formatTwiMLResponse();
    return new NextResponse(errorResponse, {
      status: 200, // Return 200 to prevent Twilio retries
      headers: { 'Content-Type': 'text/xml' }
    });
  }
}

/**
 * GET handler for webhook testing and health checks
 * Useful for verifying webhook URL is accessible
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  console.log('🔍 GET request to Twilio webhook endpoint');
  
  return NextResponse.json({
    status: 'ok',
    message: 'Twilio WhatsApp webhook endpoint is running',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
}

/**
 * Helper function to detect order-related messages
 * @param messageBody - Message content to analyze
 * @returns true if message appears to be order-related
 */
function isOrderRelatedMessage(messageBody: string): boolean {
  if (!messageBody) return false;
  
  const orderKeywords = [
    'order', 'pedir', 'quiero', 'necesito', 'want', 'need',
    'buy', 'comprar', 'purchase', 'delivery', 'entrega',
    'bottles', 'botellas', 'cases', 'cajas', 'pack', 'paquete'
  ];
  
  const lowerBody = messageBody.toLowerCase();
  return orderKeywords.some(keyword => lowerBody.includes(keyword));
}

/**
 * Helper function to detect help requests
 * @param messageBody - Message content to analyze
 * @returns true if message appears to be a help request
 */
function isHelpRequest(messageBody: string): boolean {
  if (!messageBody) return false;
  
  const helpKeywords = [
    'help', 'ayuda', 'support', 'soporte', 'how', 'como',
    'what', 'que', 'menu', 'catalog', 'catalogo', 'price', 'precio'
  ];
  
  const lowerBody = messageBody.toLowerCase();
  return helpKeywords.some(keyword => lowerBody.includes(keyword));
}

/**
 * Triggers AI agent processing for a new message
 * Calls the AI agent HTTP API to process the message in real-time
 * @param messageData - Message processing data
 */
async function triggerAIAgentProcessing(messageData: {
  messageId: string;
  customerId: string;
  conversationId: string;
  content: string;
  distributorId: string;
  channel: string;
}) {
  const AI_AGENT_URL = process.env.AI_AGENT_URL || 'http://localhost:8001';
  const endpoint = `${AI_AGENT_URL}/process-message`;
  
  console.log(`🔄 Calling AI agent at: ${endpoint}`);
  
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message_id: messageData.messageId,
        customer_id: messageData.customerId,
        conversation_id: messageData.conversationId,
        content: messageData.content,
        distributor_id: messageData.distributorId,
        channel: messageData.channel
      }),
      // Don't wait too long - this is background processing
      signal: AbortSignal.timeout(5000) // 5 second timeout
    });
    
    if (!response.ok) {
      throw new Error(`AI agent responded with status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('✅ AI agent processing queued:', result);
    
  } catch (error) {
    console.error('❌ AI agent call failed:', error);
    throw error;
  }
}


/**
 * OPTIONS handler for CORS preflight requests
 * Required for browser-based testing tools
 */
export async function OPTIONS(request: NextRequest): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Twilio-Signature',
    },
  });
}