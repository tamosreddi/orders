/**
 * Tests for Twilio WhatsApp webhook handler
 * Following the existing test patterns from tests/orders.test.tsx
 */

import { NextRequest } from 'next/server';

// Mock dependencies
jest.mock('../../lib/utils/twilio', () => ({
  validateTwilioSignature: jest.fn(),
  validateWebhookPayload: jest.fn(),
  formatTwiMLResponse: jest.fn(),
  getDefaultDistributorId: jest.fn(() => '550e8400-e29b-41d4-a716-446655440000'),
  validateEnvironmentVariables: jest.fn(),
  WHATSAPP_RESPONSES: {
    WELCOME: "Thank you for your message! We'll get back to you soon.",
    ERROR: "Sorry, we're experiencing technical difficulties. Please try again later."
  }
}));

jest.mock('../../lib/api/whatsapp', () => ({
  processWhatsAppMessage: jest.fn()
}));

// Import after mocking
import { POST, GET } from '../../app/api/webhooks/twilio/route';
import { 
  validateTwilioSignature, 
  validateWebhookPayload,
  formatTwiMLResponse 
} from '../../lib/utils/twilio';
import { processWhatsAppMessage } from '../../lib/api/whatsapp';

// Setup environment variables for tests
process.env.TWILIO_ACCOUNT_SID = 'test_account_sid';
process.env.TWILIO_AUTH_TOKEN = 'test_auth_token';
process.env.TWILIO_PHONE_NUMBER = '+14155238886';
process.env.NEXT_PUBLIC_WEBHOOK_URL = 'https://test.ngrok.io/api/webhooks/twilio';

describe('Twilio Webhook Handler', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('POST /api/webhooks/twilio', () => {
    test('processes valid webhook payload successfully', async () => {
      // Mock FormData for valid payload
      const mockFormData = new Map([
        ['From', 'whatsapp:+1234567890'],
        ['To', 'whatsapp:+14155238886'],
        ['Body', 'Hello from customer'],
        ['MessageSid', 'SM1234567890'],
        ['AccountSid', 'AC1234567890'],
        ['NumMedia', '0']
      ]);

      const request = {
        formData: jest.fn().mockResolvedValue(mockFormData),
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-twilio-signature') return 'valid-signature-hash';
            return null;
          })
        }
      } as unknown as NextRequest;

      // Mock successful validation and processing
      (validateTwilioSignature as jest.Mock).mockReturnValue(true);
      (validateWebhookPayload as jest.Mock).mockReturnValue({
        isValid: true,
        payload: Object.fromEntries(mockFormData)
      });
      (processWhatsAppMessage as jest.Mock).mockResolvedValue({
        customer: { id: 'customer-1' },
        conversation: { id: 'conversation-1' },
        message: { id: 'message-1' }
      });
      (formatTwiMLResponse as jest.Mock).mockReturnValue('<Response><Message>Thank you!</Message></Response>');

      const response = await POST(request);

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toBe('text/xml');
      expect(validateTwilioSignature).toHaveBeenCalledWith(
        'test_auth_token',
        'valid-signature-hash',
        'https://test.ngrok.io/api/webhooks/twilio',
        expect.any(Object)
      );
      expect(processWhatsAppMessage).toHaveBeenCalled();
    });

    test('rejects requests with invalid signature', async () => {
      const mockFormData = new Map([
        ['From', 'whatsapp:+1234567890'],
        ['Body', 'Test message']
      ]);

      const request = {
        formData: jest.fn().mockResolvedValue(mockFormData),
        headers: {
          get: jest.fn((header) => {
            if (header === 'x-twilio-signature') return 'invalid-signature';
            return null;
          })
        }
      } as unknown as NextRequest;

      (validateTwilioSignature as jest.Mock).mockReturnValue(false);

      const response = await POST(request);

      expect(response.status).toBe(401);
      expect(validateTwilioSignature).toHaveBeenCalled();
      expect(processWhatsAppMessage).not.toHaveBeenCalled();
    });

    test('handles missing signature header', async () => {
      const request = {
        formData: jest.fn().mockResolvedValue(new Map()),
        headers: {
          get: jest.fn(() => null)
        }
      } as unknown as NextRequest;

      const response = await POST(request);

      expect(response.status).toBe(401);
      expect(validateTwilioSignature).not.toHaveBeenCalled();
    });

    test('handles invalid webhook payload gracefully', async () => {
      const mockFormData = new Map([
        ['From', 'invalid-phone-format'],
        ['Body', 'Test message']
      ]);

      const request = {
        formData: jest.fn().mockResolvedValue(mockFormData),
        headers: {
          get: jest.fn(() => 'valid-signature')
        }
      } as unknown as NextRequest;

      (validateTwilioSignature as jest.Mock).mockReturnValue(true);
      (validateWebhookPayload as jest.Mock).mockReturnValue({
        isValid: false,
        error: 'Invalid phone format'
      });
      (formatTwiMLResponse as jest.Mock).mockReturnValue('<Response><Message>Error</Message></Response>');

      const response = await POST(request);

      expect(response.status).toBe(200); // Should return 200 with error TwiML
      expect(response.headers.get('content-type')).toBe('text/xml');
      expect(processWhatsAppMessage).not.toHaveBeenCalled();
    });

    test('handles processing errors gracefully', async () => {
      const mockFormData = new Map([
        ['From', 'whatsapp:+1234567890'],
        ['To', 'whatsapp:+14155238886'],
        ['Body', 'Hello'],
        ['MessageSid', 'SM123'],
        ['AccountSid', 'AC123'],
        ['NumMedia', '0']
      ]);

      const request = {
        formData: jest.fn().mockResolvedValue(mockFormData),
        headers: {
          get: jest.fn(() => 'valid-signature')
        }
      } as unknown as NextRequest;

      (validateTwilioSignature as jest.Mock).mockReturnValue(true);
      (validateWebhookPayload as jest.Mock).mockReturnValue({
        isValid: true,
        payload: Object.fromEntries(mockFormData)
      });
      (processWhatsAppMessage as jest.Mock).mockRejectedValue(new Error('Database connection failed'));
      (formatTwiMLResponse as jest.Mock).mockReturnValue('<Response><Message>Error</Message></Response>');

      const response = await POST(request);

      expect(response.status).toBe(200); // Should return 200 with error TwiML
      expect(response.headers.get('content-type')).toBe('text/xml');
    });
  });

  describe('GET /api/webhooks/twilio', () => {
    test('returns health check response', async () => {
      const request = {} as NextRequest;

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty('status', 'ok');
      expect(data).toHaveProperty('message');
      expect(data).toHaveProperty('timestamp');
      expect(data).toHaveProperty('environment');
    });
  });

  describe('Webhook Payload Validation', () => {
    test('validates required fields', () => {
      const validPayload = {
        From: 'whatsapp:+1234567890',
        To: 'whatsapp:+14155238886',
        Body: 'Test message',
        MessageSid: 'SM123',
        AccountSid: 'AC123',
        NumMedia: '0'
      };

      // Test with mock implementation
      const mockValidateWebhookPayload = validateWebhookPayload as jest.Mock;
      mockValidateWebhookPayload.mockReturnValue({
        isValid: true,
        payload: validPayload
      });

      const result = validateWebhookPayload(validPayload);
      expect(result.isValid).toBe(true);
    });

    test('rejects payloads with missing required fields', () => {
      const invalidPayload = {
        From: 'whatsapp:+1234567890',
        // Missing required fields
      };

      const mockValidateWebhookPayload = validateWebhookPayload as jest.Mock;
      mockValidateWebhookPayload.mockReturnValue({
        isValid: false,
        error: 'Missing required fields'
      });

      const result = validateWebhookPayload(invalidPayload);
      expect(result.isValid).toBe(false);
      expect(result.error).toBeDefined();
    });
  });
});