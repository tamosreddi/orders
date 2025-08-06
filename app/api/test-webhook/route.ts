import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    console.log('🧪 Test webhook called');
    
    const formData = await request.formData();
    const body: Record<string, any> = {};
    
    formData.forEach((value, key) => {
      body[key] = value.toString();
    });
    
    console.log('📝 Test webhook data:', body);
    
    // Check environment variable
    const useAIAgent = process.env.USE_AI_AGENT_WEBHOOK;
    console.log('🔧 USE_AI_AGENT_WEBHOOK =', useAIAgent);
    
    if (useAIAgent === 'true') {
      console.log('🤖 Would call AI agent here');
      
      // Try calling AI agent
      try {
        const aiResponse = await fetch('http://localhost:8001/health');
        console.log('✅ AI Agent reachable:', aiResponse.status);
      } catch (error) {
        console.log('❌ AI Agent not reachable:', error);
      }
    } else {
      console.log('📝 AI agent disabled');
    }
    
    return NextResponse.json({
      success: true,
      useAIAgent,
      body
    });
    
  } catch (error) {
    console.error('❌ Test webhook error:', error);
    return NextResponse.json({
      success: false,
      error: String(error)
    }, { status: 500 });
  }
}