import { renderHook, waitFor } from '@testing-library/react';
import { useHasUnreadMessages } from '../../../lib/hooks/useHasUnreadMessages';

// Mock Supabase client
jest.mock('../../../lib/supabase/client', () => ({
  supabase: {
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          eq: jest.fn(() => ({
            gt: jest.fn(() => ({
              limit: jest.fn(() => ({
                single: jest.fn()
              }))
            }))
          }))
        }))
      }))
    })),
    channel: jest.fn(() => ({
      on: jest.fn(() => ({
        subscribe: jest.fn()
      }))
    })),
    removeChannel: jest.fn()
  }
}));

describe('useHasUnreadMessages', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return initial loading state', () => {
    const { result } = renderHook(() => useHasUnreadMessages());
    
    expect(result.current.loading).toBe(true);
    expect(result.current.hasUnreadMessages).toBe(false);
    expect(result.current.error).toBe(null);
    expect(typeof result.current.refresh).toBe('function');
  });

  it('should handle no unread messages correctly', async () => {
    const mockSupabase = require('../../../lib/supabase/client').supabase;
    
    // Mock no unread messages (PGRST116 error)
    mockSupabase.from().select().eq().eq().gt().limit().single.mockResolvedValue({
      data: null,
      error: { code: 'PGRST116', message: 'No rows returned' }
    });

    const { result } = renderHook(() => useHasUnreadMessages());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasUnreadMessages).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should handle unread messages correctly', async () => {
    const mockSupabase = require('../../../lib/supabase/client').supabase;
    
    // Mock unread messages found
    mockSupabase.from().select().eq().eq().gt().limit().single.mockResolvedValue({
      data: { id: 'some-conversation-id' },
      error: null
    });

    const { result } = renderHook(() => useHasUnreadMessages());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasUnreadMessages).toBe(true);
    expect(result.current.error).toBe(null);
  });

  it('should handle errors correctly', async () => {
    const mockSupabase = require('../../../lib/supabase/client').supabase;
    
    // Mock database error
    mockSupabase.from().select().eq().eq().gt().limit().single.mockResolvedValue({
      data: null,
      error: { code: 'PGRST001', message: 'Database error' }
    });

    const { result } = renderHook(() => useHasUnreadMessages());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.hasUnreadMessages).toBe(false);
    expect(result.current.error).toContain('Database error');
  });
});