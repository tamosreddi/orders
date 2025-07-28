import twilio from 'twilio';
import { 
  TwilioWebhookPayload, 
  WhatsAppError, 
  WHATSAPP_ERROR_MESSAGES,
  isValidWhatsAppPhoneFormat,
  isTwilioWebhookPayload,
  WebhookValidationResult,
  MessageAttachment
} from '../../types/twilio';

const MessagingResponse = twilio.twiml.MessagingResponse;

/**
 * Parses phone number from Twilio WhatsApp format
 * @param twilioFormat - Format: "whatsapp:+1234567890"
 * @returns Parsed phone number: "+1234567890"
 * @throws WhatsAppError if format is invalid
 */
export function parsePhoneNumber(twilioFormat: string): string {
  // PATTERN: Validate format first, then extract (following lib/api/customers.ts pattern)
  if (!isValidWhatsAppPhoneFormat(twilioFormat)) {
    throw new WhatsAppError(
      WHATSAPP_ERROR_MESSAGES.INVALID_PHONE_FORMAT,
      'INVALID_PHONE_FORMAT',
      null,
      { From: twilioFormat } as any
    );
  }
  
  return twilioFormat.replace('whatsapp:', '');
}

/**
 * Validates Twilio webhook signature for security
 * CRITICAL: Use Twilio's validateRequest - don't implement custom validation
 * @param authToken - Twilio auth token from environment
 * @param signature - X-Twilio-Signature header value
 * @param url - Complete webhook URL (MUST be exact match)
 * @param params - Webhook parameters/body
 * @returns true if signature is valid
 */
export function validateTwilioSignature(
  authToken: string,
  signature: string,
  url: string,
  params: Record<string, any>
): boolean {
  try {
    // GOTCHA: URL must be EXACT match including protocol, domain, path, and query parameters
    return twilio.validateRequest(authToken, signature, url, params);
  } catch (error) {
    console.error('Twilio signature validation error:', error);
    return false;
  }
}

/**
 * Formats TwiML response for Twilio webhook
 * @param message - Response message to send back to customer
 * @returns XML string formatted as TwiML
 */
export function formatTwiMLResponse(message: string): string {
  const twiml = new MessagingResponse();
  twiml.message(message);
  return twiml.toString();
}

/**
 * Validates and parses Twilio webhook payload
 * @param rawPayload - Raw webhook data from request
 * @returns Validation result with parsed payload or error
 */
export function validateWebhookPayload(rawPayload: any): WebhookValidationResult {
  try {
    // Basic structure validation
    if (!isTwilioWebhookPayload(rawPayload)) {
      return {
        isValid: false,
        error: WHATSAPP_ERROR_MESSAGES.MISSING_REQUIRED_FIELDS
      };
    }

    // Phone number format validation
    if (!isValidWhatsAppPhoneFormat(rawPayload.From)) {
      return {
        isValid: false,
        error: `Invalid 'From' phone format: ${rawPayload.From}`
      };
    }

    if (!isValidWhatsAppPhoneFormat(rawPayload.To)) {
      return {
        isValid: false,
        error: `Invalid 'To' phone format: ${rawPayload.To}`
      };
    }

    // Content validation
    if (!rawPayload.Body || rawPayload.Body.trim().length === 0) {
      return {
        isValid: false,
        error: 'Message body cannot be empty'
      };
    }

    return {
      isValid: true,
      payload: rawPayload
    };

  } catch (error) {
    return {
      isValid: false,
      error: `Payload validation error: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Extracts media attachments from Twilio webhook payload
 * @param payload - Validated Twilio webhook payload
 * @returns Array of message attachments
 */
export function extractMediaAttachments(payload: TwilioWebhookPayload): MessageAttachment[] {
  const attachments: MessageAttachment[] = [];
  const numMedia = parseInt(payload.NumMedia, 10);

  if (numMedia === 0) {
    return attachments;
  }

  // Process up to 10 media items (Twilio limit)
  for (let i = 0; i < Math.min(numMedia, 10); i++) {
    const mediaUrl = payload[`MediaUrl${i}` as keyof TwilioWebhookPayload] as string;
    const mediaContentType = payload[`MediaContentType${i}` as keyof TwilioWebhookPayload] as string;

    if (mediaUrl && mediaContentType) {
      // Generate attachment metadata
      const attachment: MessageAttachment = {
        id: `${payload.MessageSid}-media-${i}`,
        type: getAttachmentType(mediaContentType),
        url: mediaUrl,
        fileName: generateFileName(mediaContentType, i),
        mimeType: mediaContentType
      };

      attachments.push(attachment);
    }
  }

  return attachments;
}

/**
 * Maps MIME type to attachment type
 * @param mimeType - MIME type from Twilio
 * @returns Standardized attachment type
 */
function getAttachmentType(mimeType: string): 'image' | 'audio' | 'file' {
  if (mimeType.startsWith('image/')) {
    return 'image';
  } else if (mimeType.startsWith('audio/')) {
    return 'audio';
  } else {
    return 'file';
  }
}

/**
 * Generates filename for media attachment
 * @param mimeType - MIME type from Twilio
 * @param index - Media index (0-9)
 * @returns Generated filename
 */
function generateFileName(mimeType: string, index: number): string {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
  const extension = getFileExtension(mimeType);
  return `whatsapp_media_${timestamp}_${index}.${extension}`;
}

/**
 * Gets file extension from MIME type
 * @param mimeType - MIME type
 * @returns File extension
 */
function getFileExtension(mimeType: string): string {
  const extensionMap: Record<string, string> = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'audio/mpeg': 'mp3',
    'audio/mp4': 'm4a',
    'audio/ogg': 'ogg',
    'audio/wav': 'wav',
    'video/mp4': 'mp4',
    'application/pdf': 'pdf',
    'text/plain': 'txt'
  };

  return extensionMap[mimeType] || 'bin';
}

/**
 * Generates auto customer name from phone number
 * @param phoneNumber - Parsed phone number (+1234567890)
 * @returns Generated business name
 */
export function generateCustomerName(phoneNumber: string): string {
  return `WhatsApp Customer ${phoneNumber}`;
}

/**
 * Generates customer code from phone number
 * @param phoneNumber - Parsed phone number (+1234567890) 
 * @returns Generated customer code
 */
export function generateCustomerCode(phoneNumber: string): string {
  // Remove + and take last 10 digits for code
  const digits = phoneNumber.replace(/\D/g, '');
  const lastTenDigits = digits.slice(-10);
  return `WA${lastTenDigits}`;
}

/**
 * Gets default distributor ID for sandbox testing
 * GOTCHA: Default to demo distributor for sandbox testing
 * @returns Distributor ID from environment or default
 */
export function getDefaultDistributorId(): string {
  const envDistributorId = process.env.DEMO_DISTRIBUTOR_ID;
  const defaultId = '550e8400-e29b-41d4-a716-446655440000'; // From customers.ts DEV_DISTRIBUTORS
  
  console.log(`🧪 WhatsApp Integration: Using distributor ID: ${envDistributorId || defaultId}`);
  
  return envDistributorId || defaultId;
}

/**
 * Handles Supabase errors specific to WhatsApp operations
 * PATTERN: Follow error handling from lib/api/customers.ts
 * @param error - Supabase error object
 * @returns WhatsAppError with user-friendly message
 */
export function handleWhatsAppSupabaseError(error: any): WhatsAppError {
  // Handle specific Supabase error codes
  if (error.code === '23505') { // Unique constraint violation
    if (error.constraint?.includes('phone')) {
      return new WhatsAppError(
        'Customer with this phone number already exists', 
        'CUSTOMER_CREATION_FAILED', 
        error
      );
    }
    if (error.constraint?.includes('customer_id') && error.constraint?.includes('channel')) {
      return new WhatsAppError(
        'Conversation already exists for this customer and channel', 
        'CONVERSATION_CREATION_FAILED', 
        error
      );
    }
  }
  
  if (error.code === 'PGRST301') { // Permission denied
    return new WhatsAppError(
      'Permission denied for WhatsApp operation', 
      'CUSTOMER_CREATION_FAILED', 
      error
    );
  }
  
  if (error.code === 'PGRST116') { // Not found
    return new WhatsAppError(
      'Customer or conversation not found', 
      'CUSTOMER_CREATION_FAILED', 
      error
    );
  }
  
  // Network or unknown errors
  return new WhatsAppError(
    WHATSAPP_ERROR_MESSAGES.UNKNOWN_WEBHOOK_ERROR, 
    'UNKNOWN_WEBHOOK_ERROR', 
    error
  );
}

/**
 * Creates standard WhatsApp response messages
 */
export const WHATSAPP_RESPONSES = {
  WELCOME: "Thank you for your message! We'll get back to you soon.",
  ORDER_RECEIVED: "Thank you for your order! We're processing it now and will confirm details shortly.",
  ERROR: "Sorry, we're experiencing technical difficulties. Please try again later.",
  MEDIA_RECEIVED: "Thank you for sharing that with us! We'll review it and get back to you.",
  HELP: "Hi! Send us your order details and we'll help you place it. You can also send photos of products you need."
};

/**
 * Validates environment variables for WhatsApp integration
 * @throws WhatsAppError if required variables are missing
 */
export function validateEnvironmentVariables(): void {
  const required = [
    'TWILIO_ACCOUNT_SID',
    'TWILIO_AUTH_TOKEN', 
    'TWILIO_PHONE_NUMBER',
    'NEXT_PUBLIC_WEBHOOK_URL'
  ];

  const missing = required.filter(envVar => !process.env[envVar]);
  
  if (missing.length > 0) {
    throw new WhatsAppError(
      `Missing required environment variables: ${missing.join(', ')}`,
      'UNKNOWN_WEBHOOK_ERROR'
    );
  }
}