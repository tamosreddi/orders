import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * POST /api/order-sessions/[sessionId]/close
 * 
 * Close an active order session and create the consolidated order
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;

    if (!sessionId) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    // Get the session details
    const { data: session, error: sessionError } = await supabase
      .from('conversation_order_sessions')
      .select(`
        id,
        conversation_id,
        distributor_id,
        status,
        collected_message_ids,
        total_messages_count,
        confidence_score
      `)
      .eq('id', sessionId)
      .single();

    if (sessionError) {
      console.error('Error fetching session:', sessionError);
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    if (session.status === 'CLOSED') {
      return NextResponse.json(
        { error: 'Session is already closed' },
        { status: 400 }
      );
    }

    // Get the conversation details
    const { data: conversation, error: conversationError } = await supabase
      .from('conversations')
      .select('customer_id, channel')
      .eq('id', session.conversation_id)
      .single();

    if (conversationError) {
      console.error('Error fetching conversation:', conversationError);
      return NextResponse.json(
        { error: 'Conversation not found' },
        { status: 404 }
      );
    }

    // Get session items
    const { data: items, error: itemsError } = await supabase
      .from('order_session_items')
      .select(`
        id,
        product_name,
        quantity,
        product_unit,
        unit_price,
        line_total,
        ai_confidence,
        original_text,
        suggested_product_id,
        matching_confidence
      `)
      .eq('session_id', sessionId)
      .eq('item_status', 'ACTIVE')
      .order('sequence_number');

    if (itemsError) {
      console.error('Error fetching session items:', itemsError);
      return NextResponse.json(
        { error: 'Failed to fetch session items' },
        { status: 500 }
      );
    }

    if (!items || items.length === 0) {
      return NextResponse.json(
        { error: 'No items found in session' },
        { status: 400 }
      );
    }

    // Transition session to REVIEWING status
    const { error: reviewingError } = await supabase
      .from('conversation_order_sessions')
      .update({
        status: 'REVIEWING',
        updated_at: new Date().toISOString()
      })
      .eq('id', sessionId);

    if (reviewingError) {
      console.error('Error updating session to REVIEWING:', reviewingError);
      return NextResponse.json(
        { error: 'Failed to update session status' },
        { status: 500 }
      );
    }

    // Calculate total amount
    const totalAmount = items.reduce((sum, item) => {
      const lineTotal = item.line_total || (item.unit_price || 0) * item.quantity;
      return sum + parseFloat(lineTotal.toString());
    }, 0);

    // Create the order
    const { data: order, error: orderError } = await supabase
      .from('orders')
      .insert({
        customer_id: conversation.customer_id,
        distributor_id: session.distributor_id,
        conversation_id: session.conversation_id,
        channel: conversation.channel || 'WHATSAPP',
        status: 'REVIEW',
        received_date: new Date().toISOString().split('T')[0],
        received_time: new Date().toTimeString().split(' ')[0],
        total_amount: totalAmount,
        additional_comment: `Consolidated from ${items.length} items across ${session.total_messages_count} messages`,
        ai_generated: true,
        ai_confidence: session.confidence_score || 0.0,
        ai_source_message_id: session.collected_message_ids?.[0] || null,
        requires_review: true,
        is_consolidated: true,
        order_session_id: sessionId
      })
      .select('id')
      .single();

    if (orderError) {
      console.error('Error creating order:', orderError);
      return NextResponse.json(
        { error: 'Failed to create order' },
        { status: 500 }
      );
    }

    // Create order products
    const orderProducts = items.map((item, index) => ({
      order_id: order.id,
      product_name: item.product_name,
      quantity: item.quantity,
      product_unit: item.product_unit || 'units',
      unit_price: item.unit_price || 0,
      line_price: item.line_total || (item.unit_price || 0) * item.quantity,
      ai_extracted: true,
      ai_confidence: item.ai_confidence || 0.0,
      ai_original_text: item.original_text || '',
      suggested_product_id: item.suggested_product_id,
      matching_confidence: item.matching_confidence,
      line_order: index + 1
    }));

    const { error: productsError } = await supabase
      .from('order_products')
      .insert(orderProducts);

    if (productsError) {
      console.error('Error creating order products:', productsError);
      // Try to clean up the order
      await supabase.from('orders').delete().eq('id', order.id);
      return NextResponse.json(
        { error: 'Failed to create order products' },
        { status: 500 }
      );
    }

    // Close the session
    const { error: closeError } = await supabase
      .from('conversation_order_sessions')
      .update({
        status: 'CLOSED',
        closed_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', sessionId);

    if (closeError) {
      console.error('Error closing session:', closeError);
      // Session will remain in REVIEWING status, but order was created
    }

    // Log the completion event
    await supabase
      .from('order_session_events')
      .insert({
        session_id: sessionId,
        event_type: 'ORDER_CREATED',
        event_data: {
          order_id: order.id,
          total_items: items.length,
          total_amount: totalAmount
        },
        ai_triggered: false
      });

    return NextResponse.json(
      {
        success: true,
        order_created: true,
        order_id: order.id,
        session_id: sessionId,
        total_items: items.length,
        total_amount: totalAmount
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Unexpected error in POST /api/order-sessions/[sessionId]/close:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}