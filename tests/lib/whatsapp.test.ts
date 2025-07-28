/**
 * Tests for WhatsApp database service layer
 * Tests the functions in lib/api/whatsapp.ts
 */

import { jest } from '@jest/globals';
import { TwilioWebhookPayload } from '../../types/twilio';

// Mock Supabase client
const mockSupabase = {
  from: jest.fn().mockReturnThis(),
  select: jest.fn().mockReturnThis(),
  insert: jest.fn().mockReturnThis(),
  update: jest.fn().mockReturnThis(),
  eq: jest.fn().mockReturnThis(),
  single: jest.fn(),
  data: null,
  error: null
};

jest.mock('../../lib/supabase/client', () => ({
  supabase: mockSupabase
}));

// Import after mocking
import {
  findOrCreateCustomer,
  findOrCreateConversation,
  createMessage,
  processWhatsAppMessage
} from '../../lib/api/whatsapp';

describe('WhatsApp Database Service Layer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSupabase.data = null;
    mockSupabase.error = null;
  });

  describe('findOrCreateCustomer', () => {
    const phoneNumber = '+1234567890';
    const distributorId = '550e8400-e29b-41d4-a716-446655440000';

    test('returns existing customer when found', async () => {
      const existingCustomer = {
        id: 'customer-123',
        business_name: 'John Doe',
        customer_code: 'WA001',
        phone_number: phoneNumber,
        distributor_id: distributorId
      };

      mockSupabase.single.mockResolvedValue({
        data: existingCustomer,
        error: null
      });

      const result = await findOrCreateCustomer(phoneNumber, distributorId);

      expect(result).toEqual({
        id: 'customer-123',
        name: 'John Doe',
        code: 'WA001',
        phone: phoneNumber,
        distributorId: distributorId
      });

      expect(mockSupabase.from).toHaveBeenCalledWith('customers');
      expect(mockSupabase.eq).toHaveBeenCalledWith('phone_number', phoneNumber);
      expect(mockSupabase.eq).toHaveBeenCalledWith('distributor_id', distributorId);
    });

    test('creates new customer when not found', async () => {
      // First query returns no customer
      mockSupabase.single.mockResolvedValueOnce({
        data: null,
        error: { code: 'PGRST116' } // Not found error
      });

      // Second query (insert) returns new customer
      const newCustomer = {
        id: 'customer-456',
        business_name: phoneNumber,
        customer_code: 'WA002',
        phone_number: phoneNumber,
        distributor_id: distributorId
      };

      mockSupabase.single.mockResolvedValueOnce({
        data: newCustomer,
        error: null
      });

      const result = await findOrCreateCustomer(phoneNumber, distributorId);

      expect(result).toEqual({
        id: 'customer-456',
        name: phoneNumber,
        code: 'WA002',
        phone: phoneNumber,
        distributorId: distributorId
      });

      expect(mockSupabase.from).toHaveBeenCalledWith('customers');
      expect(mockSupabase.insert).toHaveBeenCalledWith([{
        business_name: phoneNumber,
        phone_number: phoneNumber,
        customer_code: expect.stringMatching(/^WA\d+$/),
        distributor_id: distributorId,
        created_at: expect.any(String),
        updated_at: expect.any(String)
      }]);
    });

    test('handles database errors gracefully', async () => {
      mockSupabase.single.mockRejectedValue(new Error('Database connection failed'));

      await expect(findOrCreateCustomer(phoneNumber, distributorId))
        .rejects
        .toThrow('Failed to find or create customer: Database connection failed');
    });
  });

  describe('findOrCreateConversation', () => {
    const customerId = 'customer-123';
    const channel = 'WHATSAPP';
    const distributorId = '550e8400-e29b-41d4-a716-446655440000';

    test('returns existing conversation when found', async () => {
      const existingConversation = {
        id: 'conversation-123',
        customer_id: customerId,
        channel: 'WHATSAPP',
        status: 'ACTIVE',
        distributor_id: distributorId
      };

      mockSupabase.single.mockResolvedValue({
        data: existingConversation,
        error: null
      });

      const result = await findOrCreateConversation(customerId, channel, distributorId);

      expect(result).toEqual({
        id: 'conversation-123',
        customerId: customerId,
        channel: 'WHATSAPP',
        status: 'ACTIVE',
        distributorId: distributorId
      });

      expect(mockSupabase.from).toHaveBeenCalledWith('conversations');
      expect(mockSupabase.eq).toHaveBeenCalledWith('customer_id', customerId);
      expect(mockSupabase.eq).toHaveBeenCalledWith('channel', channel);
      expect(mockSupabase.eq).toHaveBeenCalledWith('distributor_id', distributorId);
    });

    test('creates new conversation when not found', async () => {
      // First query returns no conversation
      mockSupabase.single.mockResolvedValueOnce({
        data: null,
        error: { code: 'PGRST116' } // Not found error
      });

      // Second query (insert) returns new conversation
      const newConversation = {
        id: 'conversation-456',
        customer_id: customerId,
        channel: 'WHATSAPP',
        status: 'ACTIVE',
        distributor_id: distributorId
      };

      mockSupabase.single.mockResolvedValueOnce({
        data: newConversation,
        error: null
      });

      const result = await findOrCreateConversation(customerId, channel, distributorId);

      expect(result).toEqual({
        id: 'conversation-456',
        customerId: customerId,
        channel: 'WHATSAPP',
        status: 'ACTIVE',
        distributorId: distributorId
      });

      expect(mockSupabase.insert).toHaveBeenCalledWith([{
        customer_id: customerId,
        channel: channel,
        status: 'ACTIVE',
        distributor_id: distributorId,
        unread_count: 0,
        created_at: expect.any(String),
        updated_at: expect.any(String),
        last_message_at: expect.any(String)
      }]);
    });
  });

  describe('createMessage', () => {
    const messageData = {
      conversationId: 'conversation-123',
      content: 'Hello from WhatsApp',
      isFromCustomer: true,
      messageType: 'TEXT' as const,
      status: 'RECEIVED' as const,
      externalMessageId: 'SM123456789',
      distributorId: '550e8400-e29b-41d4-a716-446655440000'
    };

    test('creates message successfully', async () => {
      const createdMessage = {
        id: 'message-123',
        conversation_id: messageData.conversationId,
        content: messageData.content,
        is_from_customer: messageData.isFromCustomer,
        message_type: messageData.messageType,
        status: messageData.status,
        external_message_id: messageData.externalMessageId,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      mockSupabase.single.mockResolvedValue({
        data: createdMessage,
        error: null
      });

      const result = await createMessage(messageData);

      expect(result).toEqual({
        id: 'message-123',
        conversationId: messageData.conversationId,
        content: messageData.content,
        isFromCustomer: messageData.isFromCustomer,
        messageType: messageData.messageType,
        status: messageData.status,
        externalMessageId: messageData.externalMessageId,
        distributorId: messageData.distributorId,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      });

      expect(mockSupabase.from).toHaveBeenCalledWith('messages');
      expect(mockSupabase.insert).toHaveBeenCalledWith([{
        conversation_id: messageData.conversationId,
        content: messageData.content,
        is_from_customer: messageData.isFromCustomer,
        message_type: messageData.messageType,
        status: messageData.status,
        external_message_id: messageData.externalMessageId,
        attachments: [],
        ai_processed: false,
        created_at: expect.any(String),
        updated_at: expect.any(String)
      }]);
    });

    test('handles message creation errors', async () => {
      mockSupabase.single.mockRejectedValue(new Error('Insert failed'));

      await expect(createMessage(messageData))
        .rejects
        .toThrow('Failed to create message: Insert failed');
    });
  });

  describe('processWhatsAppMessage', () => {
    const mockPayload: TwilioWebhookPayload = {
      From: 'whatsapp:+1234567890',
      To: 'whatsapp:+14155238886',
      Body: 'Hello from customer',
      MessageSid: 'SM123456789',
      AccountSid: 'AC123456789',
      NumMedia: '0',
      ProfileName: 'John Doe',
      WaId: '1234567890'
    };

    const distributorId = '550e8400-e29b-41d4-a716-446655440000';

    test('processes complete WhatsApp message successfully', async () => {
      // Mock customer creation
      const mockCustomer = {
        id: 'customer-123',
        name: '+1234567890',
        code: 'WA001',
        phone: '+1234567890',
        distributorId: distributorId
      };

      // Mock conversation creation
      const mockConversation = {
        id: 'conversation-123',
        customerId: 'customer-123',
        channel: 'WHATSAPP' as const,
        status: 'ACTIVE' as const,
        distributorId: distributorId
      };

      // Mock message creation
      const mockMessage = {
        id: 'message-123',
        conversationId: 'conversation-123',
        content: 'Hello from customer',
        isFromCustomer: true,
        messageType: 'TEXT' as const,
        status: 'RECEIVED' as const,
        externalMessageId: 'SM123456789',
        distributorId: distributorId,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      };

      // Setup mocks for sequential calls
      let callCount = 0;
      mockSupabase.single.mockImplementation(() => {
        callCount++;
        switch (callCount) {
          case 1: // findOrCreateCustomer
            return Promise.resolve({ data: null, error: { code: 'PGRST116' } });
          case 2: // createCustomer
            return Promise.resolve({ 
              data: {
                id: 'customer-123',
                business_name: '+1234567890',
                customer_code: 'WA001',
                phone_number: '+1234567890',
                distributor_id: distributorId
              }, 
              error: null 
            });
          case 3: // findOrCreateConversation
            return Promise.resolve({ data: null, error: { code: 'PGRST116' } });
          case 4: // createConversation
            return Promise.resolve({ 
              data: {
                id: 'conversation-123',
                customer_id: 'customer-123',
                channel: 'WHATSAPP',
                status: 'ACTIVE',
                distributor_id: distributorId
              }, 
              error: null 
            });
          case 5: // createMessage
            return Promise.resolve({ 
              data: {
                id: 'message-123',
                conversation_id: 'conversation-123',
                content: 'Hello from customer',
                is_from_customer: true,
                message_type: 'TEXT',
                status: 'RECEIVED',
                external_message_id: 'SM123456789',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z'
              }, 
              error: null 
            });
          default:
            return Promise.resolve({ data: null, error: null });
        }
      });

      const result = await processWhatsAppMessage(mockPayload, distributorId);

      expect(result).toEqual({
        customer: mockCustomer,
        conversation: mockConversation,
        message: mockMessage
      });

      // Verify all steps were called
      expect(mockSupabase.from).toHaveBeenCalledWith('customers');
      expect(mockSupabase.from).toHaveBeenCalledWith('conversations');
      expect(mockSupabase.from).toHaveBeenCalledWith('messages');
    });

    test('handles processing errors gracefully', async () => {
      mockSupabase.single.mockRejectedValue(new Error('Database error'));

      await expect(processWhatsAppMessage(mockPayload, distributorId))
        .rejects
        .toThrow('Failed to process WhatsApp message: Database error');
    });

    test('processes messages with media attachments', async () => {
      const payloadWithMedia: TwilioWebhookPayload = {
        ...mockPayload,
        NumMedia: '1',
        MediaUrl0: 'https://api.twilio.com/media/image.jpg',
        MediaContentType0: 'image/jpeg'
      };

      // Mock successful processing
      let callCount = 0;
      mockSupabase.single.mockImplementation(() => {
        callCount++;
        switch (callCount) {
          case 1: // Customer found
            return Promise.resolve({
              data: {
                id: 'customer-123',
                business_name: '+1234567890',
                customer_code: 'WA001',
                phone_number: '+1234567890',
                distributor_id: distributorId
              },
              error: null
            });
          case 2: // Conversation found
            return Promise.resolve({
              data: {
                id: 'conversation-123',
                customer_id: 'customer-123',
                channel: 'WHATSAPP',
                status: 'ACTIVE',
                distributor_id: distributorId
              },
              error: null
            });
          case 3: // Message created
            return Promise.resolve({
              data: {
                id: 'message-123',
                conversation_id: 'conversation-123',
                content: 'Hello from customer',
                is_from_customer: true,
                message_type: 'MEDIA',
                status: 'RECEIVED',
                external_message_id: 'SM123456789',
                attachments: [{ url: 'https://api.twilio.com/media/image.jpg', type: 'image/jpeg' }],
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z'
              },
              error: null
            });
          default:
            return Promise.resolve({ data: null, error: null });
        }
      });

      const result = await processWhatsAppMessage(payloadWithMedia, distributorId);

      expect(result.message.messageType).toBe('MEDIA');
      expect(result.message.attachments).toEqual([{
        url: 'https://api.twilio.com/media/image.jpg',
        type: 'image/jpeg'
      }]);
    });
  });

  describe('Edge Cases', () => {
    test('handles empty message content', async () => {
      const emptyPayload: TwilioWebhookPayload = {
        From: 'whatsapp:+1234567890',
        To: 'whatsapp:+14155238886',
        Body: '',
        MessageSid: 'SM123456789',
        AccountSid: 'AC123456789',
        NumMedia: '0'
      };

      // Mock successful processing with empty content
      let callCount = 0;
      mockSupabase.single.mockImplementation(() => {
        callCount++;
        if (callCount <= 2) {
          return Promise.resolve({
            data: callCount === 1 ? {
              id: 'customer-123',
              business_name: '+1234567890',
              customer_code: 'WA001',
              phone_number: '+1234567890',
              distributor_id: '550e8400-e29b-41d4-a716-446655440000'
            } : {
              id: 'conversation-123',
              customer_id: 'customer-123',
              channel: 'WHATSAPP',
              status: 'ACTIVE',
              distributor_id: '550e8400-e29b-41d4-a716-446655440000'
            },
            error: null
          });
        }
        return Promise.resolve({
          data: {
            id: 'message-123',
            conversation_id: 'conversation-123',
            content: '',
            is_from_customer: true,
            message_type: 'TEXT',
            status: 'RECEIVED',
            external_message_id: 'SM123456789',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          },
          error: null
        });
      });

      const result = await processWhatsAppMessage(emptyPayload, '550e8400-e29b-41d4-a716-446655440000');

      expect(result.message.content).toBe('');
      expect(result.message.messageType).toBe('TEXT');
    });

    test('handles very long phone numbers', async () => {
      const longPhoneNumber = '+123456789012345678901234567890';
      
      mockSupabase.single.mockResolvedValueOnce({
        data: null,
        error: { code: 'PGRST116' }
      });

      mockSupabase.single.mockResolvedValueOnce({
        data: {
          id: 'customer-123',
          business_name: longPhoneNumber,
          customer_code: 'WA001',
          phone_number: longPhoneNumber,
          distributor_id: '550e8400-e29b-41d4-a716-446655440000'
        },
        error: null
      });

      const result = await findOrCreateCustomer(longPhoneNumber, '550e8400-e29b-41d4-a716-446655440000');

      expect(result.phone).toBe(longPhoneNumber);
      expect(result.name).toBe(longPhoneNumber);
    });
  });
});