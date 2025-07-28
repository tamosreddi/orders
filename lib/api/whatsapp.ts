import { supabase } from '../supabase/client';
import type { Database } from '../supabase/types';
import { Customer } from '../../types/customer';
import { Conversation } from '../../app/messages/types/conversation';
import { Message, MessageAttachment } from '../../app/messages/types/message';
import { 
  TwilioWebhookPayload, 
  WhatsAppCustomer, 
  WhatsAppMessage,
  WhatsAppError,
  WHATSAPP_ERROR_MESSAGES 
} from '../../types/twilio';
import { 
  parsePhoneNumber, 
  generateCustomerName, 
  generateCustomerCode,
  handleWhatsAppSupabaseError,
  extractMediaAttachments
} from '../utils/twilio';

// PATTERN: Follow error handling from lib/api/customers.ts
const CUSTOMER_ERROR_MESSAGES = {
  NETWORK_ERROR: 'Connection failed. Please check your internet and try again',
  VALIDATION_ERROR: 'Please check the highlighted fields',
  UNKNOWN_ERROR: 'Something went wrong. Please try again',
  PERMISSION_DENIED: 'You do not have permission to perform this action',
  CUSTOMER_NOT_FOUND: 'Customer not found'
} as const;

// Database types
type CustomerRow = Database['public']['Tables']['customers']['Row'];
type CustomerInsert = Database['public']['Tables']['customers']['Insert'];
type ConversationRow = Database['public']['Tables']['conversations']['Row'];
type ConversationInsert = Database['public']['Tables']['conversations']['Insert'];
type MessageRow = Database['public']['Tables']['messages']['Row'];
type MessageInsert = Database['public']['Tables']['messages']['Insert'];

/**
 * Gets the current distributor ID for WhatsApp operations
 * PATTERN: Follow lib/api/customers.ts getCurrentDistributorId pattern
 */
function getCurrentDistributorId(): string {
  // For development, use the first distributor from existing pattern
  const DEV_DISTRIBUTOR_ID = '550e8400-e29b-41d4-a716-446655440000';
  
  // TODO: This should come from useAuth() hook when called from React components
  // For now, return the development distributor ID for testing
  console.log(`🧪 WhatsApp Integration: Using distributor "${DEV_DISTRIBUTOR_ID}"`);
  
  return DEV_DISTRIBUTOR_ID;
}

/**
 * Converts Supabase customer row to frontend Customer type
 * PATTERN: Mirror mapSupabaseCustomerToFrontend from customers.ts
 */
function mapSupabaseCustomerToFrontend(customerRow: CustomerRow): Customer {
  return {
    id: customerRow.id,
    name: customerRow.business_name,
    customerName: customerRow.contact_person_name || undefined,
    avatar: customerRow.avatar_url || '/logos/default-avatar.png',
    code: customerRow.customer_code,
    labels: [], // WhatsApp customers start with no labels
    lastOrdered: customerRow.last_ordered_date,
    expectedOrder: customerRow.expected_order_date,
    status: customerRow.status,
    invitationStatus: customerRow.invitation_status,
    email: customerRow.email,
    phone: customerRow.phone || undefined,
    address: customerRow.address || undefined,
    joinedDate: customerRow.joined_date || customerRow.created_at.split('T')[0],
    totalOrders: customerRow.total_orders,
    totalSpent: customerRow.total_spent
  };
}

/**
 * Converts Supabase conversation row to frontend Conversation type
 */
function mapSupabaseConversationToFrontend(
  conversationRow: ConversationRow & { customers: CustomerRow }
): Conversation {
  return {
    id: conversationRow.id,
    customerId: conversationRow.customer_id,
    customer: {
      name: conversationRow.customers.business_name,
      avatar: conversationRow.customers.avatar_url || '/logos/default-avatar.png',
      code: conversationRow.customers.customer_code
    },
    channel: conversationRow.channel as 'WHATSAPP' | 'SMS' | 'EMAIL',
    status: conversationRow.status as 'ACTIVE' | 'ARCHIVED',
    lastMessageAt: conversationRow.last_message_at || conversationRow.created_at,
    unreadCount: conversationRow.unread_count || 0,
    lastMessage: {
      content: '',
      isFromCustomer: false
    },
    aiContextSummary: conversationRow.ai_context_summary || undefined,
    distributorId: getCurrentDistributorId(),
    createdAt: conversationRow.created_at,
    updatedAt: conversationRow.updated_at
  };
}

/**
 * Finds existing customer by phone number or creates new one
 * PATTERN: Use upsert to handle race conditions (as mentioned in PRP)
 * @param phoneNumber - Parsed phone number (+1234567890)
 * @param distributorId - Distributor ID for multi-tenant isolation
 * @returns Customer record
 * @throws WhatsAppError if operation fails
 */
export async function findOrCreateCustomer(
  phoneNumber: string, 
  distributorId: string
): Promise<Customer> {
  try {
    console.log(`🔍 Finding or creating customer for phone: ${phoneNumber}`);
    
    // PATTERN: Always validate input first (see lib/api/customers.ts)
    if (!phoneNumber || !phoneNumber.startsWith('+')) {
      throw new WhatsAppError(
        WHATSAPP_ERROR_MESSAGES.INVALID_PHONE_FORMAT,
        'INVALID_PHONE_FORMAT',
        null
      );
    }

    if (!distributorId) {
      throw new WhatsAppError(
        'Missing distributor ID for customer lookup',
        'CUSTOMER_CREATION_FAILED'
      );
    }

    // First, try to find existing customer by phone number
    const { data: existingCustomer, error: findError } = await supabase
      .from('customers')
      .select('*')
      .eq('phone', phoneNumber)
      .eq('distributor_id', distributorId)
      .single();

    if (findError && findError.code !== 'PGRST116') { // PGRST116 = not found
      console.error('Error finding customer:', findError);
      throw handleWhatsAppSupabaseError(findError);
    }

    if (existingCustomer) {
      console.log(`✅ Found existing customer: ${existingCustomer.id}`);
      return mapSupabaseCustomerToFrontend(existingCustomer);
    }

    // Customer doesn't exist, create new one
    console.log(`➕ Creating new customer for phone: ${phoneNumber}`);
    
    const customerInsert: CustomerInsert = {
      distributor_id: distributorId,
      business_name: generateCustomerName(phoneNumber),
      contact_person_name: phoneNumber, // Use phone as fallback name
      customer_code: generateCustomerCode(phoneNumber),
      email: `whatsapp+${phoneNumber.replace('+', '')}@temp.orderagent.com`, // Generate temp email for WhatsApp customers
      phone: phoneNumber,
      address: null,
      avatar_url: '/logos/default-avatar.png',
      status: 'ORDERING', // WhatsApp customers are likely to order
      invitation_status: 'ACTIVE', // No invitation needed for WhatsApp
      joined_date: new Date().toISOString(),
      total_orders: 0,
      total_spent: 0
    };

    const { data: newCustomer, error: createError } = await supabase
      .from('customers')
      .insert(customerInsert)
      .select()
      .single();

    if (createError) {
      console.error('Error creating customer:', createError);
      throw handleWhatsAppSupabaseError(createError);
    }

    console.log(`✅ Created new customer: ${newCustomer.id}`);
    return mapSupabaseCustomerToFrontend(newCustomer);

  } catch (error) {
    console.error('Error in findOrCreateCustomer:', error);
    if (error instanceof WhatsAppError) {
      throw error;
    }
    throw handleWhatsAppSupabaseError(error);
  }
}

/**
 * Finds existing conversation or creates new one for WhatsApp channel
 * @param customerId - Customer ID
 * @param channel - Communication channel (WHATSAPP)
 * @param distributorId - Distributor ID for multi-tenant isolation
 * @returns Conversation record
 * @throws WhatsAppError if operation fails
 */
export async function findOrCreateConversation(
  customerId: string, 
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL',
  distributorId: string
): Promise<Conversation> {
  try {
    console.log(`🔍 Finding or creating conversation for customer: ${customerId}, channel: ${channel}`);

    // PATTERN: Validate input first
    if (!customerId || !channel || !distributorId) {
      throw new WhatsAppError(
        'Missing required parameters for conversation lookup',
        'CONVERSATION_CREATION_FAILED'
      );
    }

    // First, try to find existing conversation
    const { data: existingConversation, error: findError } = await supabase
      .from('conversations')
      .select(`
        *,
        customers!inner (
          id,
          distributor_id,
          business_name,
          contact_person_name,
          customer_code,
          email,
          phone,
          address,
          avatar_url,
          status,
          invitation_status,
          joined_date,
          last_ordered_date,
          expected_order_date,
          total_orders,
          total_spent,
          created_at,
          updated_at
        )
      `)
      .eq('customer_id', customerId)
      .eq('channel', channel)
      .single();

    if (findError && findError.code !== 'PGRST116') { // PGRST116 = not found
      console.error('Error finding conversation:', findError);
      throw handleWhatsAppSupabaseError(findError);
    }

    if (existingConversation) {
      console.log(`✅ Found existing conversation: ${existingConversation.id}`);
      return mapSupabaseConversationToFrontend(existingConversation);
    }

    // Conversation doesn't exist, create new one
    console.log(`➕ Creating new conversation for customer: ${customerId}, channel: ${channel}`);
    
    const conversationInsert: ConversationInsert = {
      customer_id: customerId,
      distributor_id: distributorId,
      channel,
      status: 'ACTIVE',
      unread_count: 0,
      last_message_at: new Date().toISOString(),
      ai_context_summary: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const { data: newConversation, error: createError } = await supabase
      .from('conversations')
      .insert(conversationInsert)
      .select(`
        *,
        customers!inner (
          id,
          distributor_id,
          business_name,
          contact_person_name,
          customer_code,
          email,
          phone,
          address,
          avatar_url,
          status,
          invitation_status,
          joined_date,
          last_ordered_date,
          expected_order_date,
          total_orders,
          total_spent,
          created_at,
          updated_at
        )
      `)
      .single();

    if (createError) {
      console.error('Error creating conversation:', createError);
      throw handleWhatsAppSupabaseError(createError);
    }

    console.log(`✅ Created new conversation: ${newConversation.id}`);
    return mapSupabaseConversationToFrontend(newConversation);

  } catch (error) {
    console.error('Error in findOrCreateConversation:', error);
    if (error instanceof WhatsAppError) {
      throw error;
    }
    throw handleWhatsAppSupabaseError(error);
  }
}

/**
 * Creates a new message in the database
 * @param messageData - Message data to insert
 * @returns Created message
 * @throws WhatsAppError if operation fails
 */
export async function createMessage(messageData: {
  conversationId: string;
  content: string;
  isFromCustomer: boolean;
  messageType?: 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE';
  attachments?: MessageAttachment[];
  externalMessageId?: string;
  externalMetadata?: any;
  distributorId: string;
}): Promise<Message> {
  try {
    console.log(`➕ Creating message for conversation: ${messageData.conversationId}`);

    // PATTERN: Validate input first
    if (!messageData.conversationId || !messageData.content || messageData.distributorId === undefined) {
      throw new WhatsAppError(
        'Missing required parameters for message creation',
        'MESSAGE_STORAGE_FAILED'
      );
    }

    const messageInsert: MessageInsert = {
      conversation_id: messageData.conversationId,
      content: messageData.content,
      is_from_customer: messageData.isFromCustomer,
      message_type: messageData.messageType || 'TEXT',
      status: 'SENT',
      attachments: (messageData.attachments || []) as any,
      ai_processed: false,
      ai_confidence: null,
      ai_extracted_intent: null,
      ai_extracted_products: null,
      ai_suggested_responses: JSON.stringify([]),
      order_context_id: null,
      external_message_id: messageData.externalMessageId || null,
    };

    const { data: newMessage, error: createError } = await supabase
      .from('messages')
      .insert(messageInsert)
      .select()
      .single();

    if (createError) {
      console.error('Error creating message:', createError);
      throw handleWhatsAppSupabaseError(createError);
    }

    // Update conversation's last_message_at and increment unread count if from customer
    if (messageData.isFromCustomer) {
      // Get current unread count first
      const { data: currentConv } = await supabase
        .from('conversations')
        .select('unread_count')
        .eq('id', messageData.conversationId)
        .single();

      const { error: updateError } = await supabase
        .from('conversations')
        .update({ 
          last_message_at: new Date().toISOString(),
          unread_count: (currentConv?.unread_count || 0) + 1,
          updated_at: new Date().toISOString()
        })
        .eq('id', messageData.conversationId);

      if (updateError) {
        console.warn('Failed to update conversation metadata:', updateError);
        // Don't throw error here as message was created successfully
      }
    } else {
      // Just update last_message_at for outbound messages
      const { error: updateError } = await supabase
        .from('conversations')
        .update({ 
          last_message_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .eq('id', messageData.conversationId);

      if (updateError) {
        console.warn('Failed to update conversation timestamp:', updateError);
      }
    }

    console.log(`✅ Created message: ${newMessage.id}`);

    // Transform to frontend format
    const frontendMessage: Message = {
      id: newMessage.id,
      conversationId: newMessage.conversation_id,
      content: newMessage.content,
      isFromCustomer: newMessage.is_from_customer,
      messageType: newMessage.message_type as 'TEXT' | 'IMAGE' | 'AUDIO' | 'FILE' | 'ORDER_CONTEXT',
      status: newMessage.status as 'SENT' | 'DELIVERED' | 'READ',
      attachments: (newMessage.attachments || []) as unknown as MessageAttachment[],
      aiProcessed: newMessage.ai_processed || false,
      aiConfidence: newMessage.ai_confidence || undefined,
      aiExtractedIntent: newMessage.ai_extracted_intent || undefined,
      aiExtractedProducts: newMessage.ai_extracted_products ? JSON.parse(JSON.stringify(newMessage.ai_extracted_products)) : undefined,
      aiSuggestedResponses: newMessage.ai_suggested_responses ? JSON.parse(JSON.stringify(newMessage.ai_suggested_responses)) : undefined,
      orderContextId: newMessage.order_context_id || undefined,
      distributorId: messageData.distributorId,
      externalMessageId: newMessage.external_message_id || undefined,
      createdAt: newMessage.created_at,
      updatedAt: newMessage.updated_at
    };

    return frontendMessage;

  } catch (error) {
    console.error('Error in createMessage:', error);
    if (error instanceof WhatsAppError) {
      throw error;
    }
    throw handleWhatsAppSupabaseError(error);
  }
}

/**
 * Processes complete WhatsApp webhook payload and stores all data
 * SEQUENCE: Customer -> Conversation -> Message (no transactions available)
 * @param payload - Validated Twilio webhook payload
 * @param distributorId - Distributor ID for multi-tenant isolation
 * @returns Created message with full context
 * @throws WhatsAppError if any step fails
 */
export async function processWhatsAppMessage(
  payload: TwilioWebhookPayload,
  distributorId: string
): Promise<{
  customer: Customer;
  conversation: Conversation;
  message: Message;
}> {
  try {
    console.log(`🔄 Processing WhatsApp message from: ${payload.From}`);
    
    // Step 1: Parse phone number
    const phoneNumber = parsePhoneNumber(payload.From);
    console.log(`📱 Parsed phone number: ${phoneNumber}`);

    // Step 2: Find or create customer
    const customer = await findOrCreateCustomer(phoneNumber, distributorId);
    console.log(`👤 Customer resolved: ${customer.id}`);

    // Step 3: Find or create conversation
    const conversation = await findOrCreateConversation(customer.id, 'WHATSAPP', distributorId);
    console.log(`💬 Conversation resolved: ${conversation.id}`);

    // Step 4: Extract media attachments
    const attachments = extractMediaAttachments(payload);
    console.log(`📎 Extracted ${attachments.length} media attachments`);

    // Step 5: Create message
    const message = await createMessage({
      conversationId: conversation.id,
      content: payload.Body,
      isFromCustomer: true,
      messageType: attachments.length > 0 ? 'IMAGE' : 'TEXT', // Simplified for now
      attachments,
      externalMessageId: payload.MessageSid,
      externalMetadata: payload,
      distributorId
    });
    console.log(`💬 Message created: ${message.id}`);

    console.log(`✅ WhatsApp message processing complete`);

    return {
      customer,
      conversation,
      message
    };

  } catch (error) {
    console.error('Error processing WhatsApp message:', error);
    if (error instanceof WhatsAppError) {
      throw error;
    }
    throw handleWhatsAppSupabaseError(error);
  }
}

/**
 * Gets customer by phone number for lookup operations
 * @param phoneNumber - Parsed phone number (+1234567890)
 * @param distributorId - Distributor ID for multi-tenant isolation
 * @returns Customer or null if not found
 */
export async function getCustomerByPhone(
  phoneNumber: string,
  distributorId: string
): Promise<Customer | null> {
  try {
    const { data: customer, error } = await supabase
      .from('customers')
      .select('*')
      .eq('phone', phoneNumber)
      .eq('distributor_id', distributorId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return null; // Customer not found
      }
      throw handleWhatsAppSupabaseError(error);
    }

    return mapSupabaseCustomerToFrontend(customer);

  } catch (error) {
    console.error('Error getting customer by phone:', error);
    if (error instanceof WhatsAppError) {
      throw error;
    }
    throw handleWhatsAppSupabaseError(error);
  }
}