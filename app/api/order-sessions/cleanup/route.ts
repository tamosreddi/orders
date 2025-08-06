import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * POST /api/order-sessions/cleanup
 * 
 * Clean up expired order sessions
 * This endpoint should be called periodically (e.g., via cron job)
 */
export async function POST(request: NextRequest) {
  try {
    // Call the database function to close timed out sessions
    const { data: result, error } = await supabase.rpc('close_timed_out_sessions');

    if (error) {
      console.error('Error calling close_timed_out_sessions:', error);
      return NextResponse.json(
        { error: 'Failed to cleanup sessions' },
        { status: 500 }
      );
    }

    const sessionsClosed = result || 0;

    // Get some additional stats about the cleanup
    const { data: stats, error: statsError } = await supabase
      .from('conversation_order_sessions')
      .select('status', { count: 'exact' });

    let statusCounts = {};
    if (!statsError && stats) {
      statusCounts = stats.reduce((acc: any, session: any) => {
        acc[session.status] = (acc[session.status] || 0) + 1;
        return acc;
      }, {});
    }

    return NextResponse.json(
      {
        success: true,
        sessions_closed: sessionsClosed,
        timestamp: new Date().toISOString(),
        status_counts: statusCounts
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Unexpected error in POST /api/order-sessions/cleanup:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/order-sessions/cleanup
 * 
 * Get cleanup statistics without performing cleanup
 */
export async function GET(request: NextRequest) {
  try {
    // Get expired sessions count
    const { data: expiredSessions, error: expiredError } = await supabase
      .from('conversation_order_sessions')
      .select('id', { count: 'exact' })
      .in('status', ['ACTIVE', 'COLLECTING'])
      .lte('expires_at', new Date().toISOString());

    if (expiredError) {
      console.error('Error fetching expired sessions:', expiredError);
      return NextResponse.json(
        { error: 'Failed to fetch expired sessions' },
        { status: 500 }
      );
    }

    // Get all sessions status counts
    const { data: allSessions, error: allError } = await supabase
      .from('conversation_order_sessions')
      .select('status', { count: 'exact' });

    let statusCounts = {};
    if (!allError && allSessions) {
      statusCounts = allSessions.reduce((acc: any, session: any) => {
        acc[session.status] = (acc[session.status] || 0) + 1;
        return acc;
      }, {});
    }

    return NextResponse.json(
      {
        expired_sessions_count: expiredSessions?.length || 0,
        status_counts: statusCounts,
        timestamp: new Date().toISOString()
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Unexpected error in GET /api/order-sessions/cleanup:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}