/**
 * Twilio WhatsApp webhook payload structure
 * Based on Twilio WhatsApp Sandbox API documentation
 * @see https://www.twilio.com/docs/messaging/guides/webhook-request
 */
export interface TwilioWebhookPayload {
  // Core message fields
  From: string;           // "whatsapp:+1234567890" - sender's WhatsApp number
  To: string;             // "whatsapp:+14155238886" - recipient's WhatsApp number  
  Body: string;           // Message content text
  MessageSid: string;     // "SMxxxxxxxxxxxx" - unique message identifier
  AccountSid: string;     // "ACxxxxxxxxxxxx" - Twilio account identifier
  
  // Media fields
  NumMedia: string;       // "0" or number as string - count of media attachments
  MediaUrl0?: string;     // First media URL if present
  MediaContentType0?: string; // MIME type of first media (image/jpeg, etc.)
  MediaUrl1?: string;     // Second media URL if present
  MediaContentType1?: string; // MIME type of second media
  // ... up to 10 media items supported
  
  // Optional metadata fields
  Timestamp?: string;     // ISO timestamp when message was sent
  ProfileName?: string;   // WhatsApp profile name of sender
  WaId?: string;         // WhatsApp ID of sender (without whatsapp: prefix)
  
  // Location fields (if location is shared)
  Latitude?: string;      // Latitude coordinate
  Longitude?: string;     // Longitude coordinate
  Address?: string;       // Address if available
  
  // Additional Twilio fields that may be present
  ForwardedFrom?: string; // If message was forwarded
  Forwarded?: string;     // "true" if forwarded
  ButtonText?: string;    // Text of button if interactive message
  ButtonPayload?: string; // Payload of button if interactive message
}

/**
 * Parsed WhatsApp message extending the base Message interface
 * Includes WhatsApp-specific metadata and external message tracking
 */
export interface WhatsAppMessage {
  // Base message fields
  id: string;
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE';
  status: 'SENT' | 'DELIVERED' | 'READ';
  attachments: MessageAttachment[];
  
  // WhatsApp-specific fields
  externalMessageId: string; // Twilio MessageSid for tracking
  externalMetadata: TwilioWebhookPayload; // Raw Twilio payload for debugging
  phoneNumber: string;       // Parsed phone number from whatsapp:+1234567890
  profileName?: string;      // WhatsApp profile name if available
  waId?: string;            // WhatsApp ID if available
  
  // Multi-tenant isolation
  distributorId: string;
  
  // AI processing (inherited from Message interface)
  aiProcessed: boolean;
  aiConfidence?: number;
  aiExtractedIntent?: string;
  aiExtractedProducts?: any[];
  aiSuggestedResponses?: string[];
  
  // Timestamps
  createdAt: string;
  updatedAt: string;
}

/**
 * WhatsApp customer data structure for automatic customer creation
 */
export interface WhatsAppCustomer {
  phoneNumber: string;    // Parsed from "whatsapp:+1234567890"  
  businessName: string;   // Auto-generated: "WhatsApp Customer +1234567890"
  contactPersonName: string; // Use phone number as fallback
  distributorId: string;  // Multi-tenant isolation
  avatar?: string;        // Default avatar
  customerCode?: string;  // Auto-generated customer code
}

/**
 * Message attachment structure for WhatsApp media
 */
export interface MessageAttachment {
  id: string;
  type: 'image' | 'audio' | 'file';
  url: string;            // Twilio media URL
  fileName: string;       // Generated filename
  fileSize?: number;      // File size in bytes if available
  mimeType: string;       // From MediaContentTypeX field
}

/**
 * Type guards for validating Twilio webhook payloads
 */
export function isTwilioWebhookPayload(payload: any): payload is TwilioWebhookPayload {
  return (
    typeof payload === 'object' &&
    payload !== null &&
    typeof payload.From === 'string' &&
    typeof payload.To === 'string' &&
    typeof payload.Body === 'string' &&
    typeof payload.MessageSid === 'string' &&
    typeof payload.AccountSid === 'string' &&
    typeof payload.NumMedia === 'string' &&
    payload.From.startsWith('whatsapp:') &&
    payload.To.startsWith('whatsapp:')
  );
}

/**
 * Type guard for validating phone number format
 */
export function isValidWhatsAppPhoneFormat(phoneNumber: string): boolean {
  return (
    typeof phoneNumber === 'string' &&
    phoneNumber.startsWith('whatsapp:+') &&
    phoneNumber.length > 12 && // At least "whatsapp:+1X"
    /^whatsapp:\+\d{10,15}$/.test(phoneNumber) // E.164 format
  );
}

/**
 * Webhook validation result structure
 */
export interface WebhookValidationResult {
  isValid: boolean;
  error?: string;
  payload?: TwilioWebhookPayload;
}

/**
 * Error types specific to WhatsApp integration
 */
export const WHATSAPP_ERROR_MESSAGES = {
  INVALID_PHONE_FORMAT: 'Invalid WhatsApp phone number format',
  MISSING_REQUIRED_FIELDS: 'Missing required fields in webhook payload',
  SIGNATURE_VALIDATION_FAILED: 'Twilio signature validation failed',
  CUSTOMER_CREATION_FAILED: 'Failed to create customer from phone number',
  CONVERSATION_CREATION_FAILED: 'Failed to create or find conversation',
  MESSAGE_STORAGE_FAILED: 'Failed to store message in database',
  MEDIA_DOWNLOAD_FAILED: 'Failed to download media attachment',
  UNKNOWN_WEBHOOK_ERROR: 'Unknown error processing webhook'
} as const;

/**
 * WhatsApp-specific error class
 */
export class WhatsAppError extends Error {
  constructor(
    message: string,
    public code: keyof typeof WHATSAPP_ERROR_MESSAGES,
    public originalError?: any,
    public payload?: TwilioWebhookPayload
  ) {
    super(message);
    this.name = 'WhatsAppError';
  }
}

/**
 * Configuration interface for WhatsApp integration
 */
export interface WhatsAppConfig {
  twilioAccountSid: string;
  twilioAuthToken: string;
  twilioPhoneNumber: string;
  webhookUrl: string;
  defaultDistributorId: string; // For sandbox testing
  maxMediaSizeMB: number;
  supportedMediaTypes: string[];
}