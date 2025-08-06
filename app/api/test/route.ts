import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  return NextResponse.json({ message: 'Test route working!' }, { status: 200 });
}

export async function POST(request: NextRequest) {
  return NextResponse.json({ message: 'POST test route working!' }, { status: 200 });
}