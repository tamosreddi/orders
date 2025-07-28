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
    const signature = request.headers.get('x-twilio-signature');
    if (!signature) {
      console.error('❌ Missing Twilio signature header');
      return new NextResponse('Missing signature', { status: 401 });
    }

    // Construct the exact URL Twilio used to send the webhook
    const url = process.env.NEXT_PUBLIC_WEBHOOK_URL;
    if (!url) {
      console.error('❌ Missing webhook URL configuration');
      return new NextResponse('Configuration error', { status: 500 });
    }

    const isSignatureValid = validateTwilioSignature(
      process.env.TWILIO_AUTH_TOKEN!,
      signature,
      url,
      payload
    );

    if (!isSignatureValid) {
      console.error('❌ Twilio signature validation failed');
      return new NextResponse('Unauthorized', { status: 401 });
    }

    console.log('✅ Twilio signature validated');

    // Validate webhook payload structure
    const validationResult = validateWebhookPayload(payload);
    if (!validationResult.isValid) {
      console.error('❌ Invalid webhook payload:', validationResult.error);
      
      // Return TwiML error response
      const errorResponse = formatTwiMLResponse(WHATSAPP_RESPONSES.ERROR);
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

    // Determine appropriate response based on message content and media
    let responseMessage = WHATSAPP_RESPONSES.WELCOME;
    
    // Check for media attachments
    if (parseInt(validatedPayload.NumMedia, 10) > 0) {
      responseMessage = WHATSAPP_RESPONSES.MEDIA_RECEIVED;
    }
    // Check for order-related keywords
    else if (isOrderRelatedMessage(validatedPayload.Body)) {
      responseMessage = WHATSAPP_RESPONSES.ORDER_RECEIVED;
    }
    // Check for help requests
    else if (isHelpRequest(validatedPayload.Body)) {
      responseMessage = WHATSAPP_RESPONSES.HELP;
    }

    // CRITICAL: Return TwiML XML response (Twilio requirement)
    const twimlResponse = formatTwiMLResponse(responseMessage);
    
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
      
      // Return appropriate TwiML error response
      const errorResponse = formatTwiMLResponse(WHATSAPP_RESPONSES.ERROR);
      return new NextResponse(errorResponse, {
        status: 200, // Return 200 to prevent Twilio retries for application errors
        headers: { 'Content-Type': 'text/xml' }
      });
    }

    // Handle unexpected errors
    console.error('Unexpected error in webhook processing:', error);
    
    // PATTERN: Log error but return generic message for security
    const errorResponse = formatTwiMLResponse(WHATSAPP_RESPONSES.ERROR);
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