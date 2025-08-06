import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * POST /api/order-sessions/[sessionId]/cancel
 * 
 * Cancel an active order session without creating an order
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
      .select('id, status')
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

    // Close/cancel the session
    const { error: cancelError } = await supabase
      .from('conversation_order_sessions')
      .update({
        status: 'CLOSED',
        closed_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', sessionId);

    if (cancelError) {
      console.error('Error cancelling session:', cancelError);
      return NextResponse.json(
        { error: 'Failed to cancel session' },
        { status: 500 }
      );
    }

    // Log the cancellation event
    await supabase
      .from('order_session_events')
      .insert({
        session_id: sessionId,
        event_type: 'SESSION_CLOSED',
        event_data: {
          reason: 'cancelled_by_user',
          cancelled_at: new Date().toISOString()
        },
        ai_triggered: false
      });

    return NextResponse.json(
      {
        success: true,
        session_id: sessionId,
        status: 'CLOSED',
        cancelled: true
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Unexpected error in POST /api/order-sessions/[sessionId]/cancel:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}