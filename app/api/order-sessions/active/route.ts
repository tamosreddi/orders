import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic';

// Initialize Supabase client with service role key for API routes
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase environment variables');
}

const supabase = createClient(
  supabaseUrl || '',
  supabaseServiceKey || ''
);

/**
 * GET /api/order-sessions/active?conversationId=xxx
 * 
 * Fetch the active order session for a conversation
 */
export async function GET(request: NextRequest) {
  try {
    // Check if Supabase is properly configured
    if (!supabaseUrl || !supabaseServiceKey) {
      console.log('Order sessions API: Supabase not configured, returning null');
      return NextResponse.json(null, { status: 200 });
    }

    const conversationId = request.nextUrl.searchParams.get('conversationId');

    if (!conversationId) {
      return NextResponse.json(
        { error: 'Conversation ID is required' },
        { status: 400 }
      );
    }

    // Check if conversation_order_sessions table exists
    // If not, return null (no active session) gracefully
    try {
      // Get active order session
      const { data: session, error: sessionError } = await supabase
        .from('conversation_order_sessions')
        .select(`
          id,
          status,
          started_at,
          last_activity_at,
          expires_at,
          total_messages_count,
          confidence_score,
          session_metadata
        `)
        .eq('conversation_id', conversationId)
        .in('status', ['ACTIVE', 'COLLECTING'])
        .gt('expires_at', new Date().toISOString())
        .order('created_at', { ascending: false })
        .limit(1)
        .single();

      if (sessionError && sessionError.code !== 'PGRST116') { // PGRST116 = no rows found
        console.error('Error fetching active session:', sessionError);
        return NextResponse.json(
          { error: 'Failed to fetch active session' },
          { status: 500 }
        );
      }

      if (!session) {
        return NextResponse.json(null, { status: 200 });
      }

      // Get session items
      const { data: items, error: itemsError } = await supabase
        .from('order_session_items')
        .select(`
          id,
          product_name,
          quantity,
          product_unit,
          ai_confidence,
          original_text,
          sequence_number
        `)
        .eq('session_id', session.id)
        .eq('item_status', 'ACTIVE')
        .order('sequence_number');

      if (itemsError) {
        console.error('Error fetching session items:', itemsError);
        // Continue without items if there's an error
      }

      // Combine session with items
      const response = {
        ...session,
        items: items || []
      };

      return NextResponse.json(response, { status: 200 });
      
    } catch (tableError: any) {
      // If table doesn't exist, return null gracefully
      if (tableError?.code === 'PGRST102' || tableError?.message?.includes('relation') || tableError?.message?.includes('does not exist')) {
        console.log('Order sessions table does not exist yet - returning null');
        return NextResponse.json(null, { status: 200 });
      }
      throw tableError; // Re-throw other errors
    }

  } catch (error) {
    console.error('Unexpected error in GET /api/order-sessions/active:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}