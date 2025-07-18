# Security Guide - Messages Page AI Integration

## Multi-Tenant Security Architecture

The Messages page implements enterprise-grade security with complete data isolation between distributors to ensure business data privacy and compliance.

## Database Security

### Row Level Security (RLS)

**Automatic Data Isolation:**
- Every table includes `distributor_id` for complete tenant separation
- RLS policies automatically filter queries by current distributor context
- Users can only access data belonging to their distributor
- All database operations respect multi-tenant boundaries

**RLS Policy Examples:**
```sql
-- Messages table RLS policy
CREATE POLICY "Users can only access their distributor's messages" 
ON messages FOR ALL 
USING (distributor_id = auth.jwt() ->> 'distributor_id');

-- Conversations table RLS policy  
CREATE POLICY "Users can only access their distributor's conversations"
ON conversations FOR ALL
USING (distributor_id = auth.jwt() ->> 'distributor_id');

-- Orders table RLS policy
CREATE POLICY "Users can only access their distributor's orders"
ON orders FOR ALL  
USING (distributor_id = auth.jwt() ->> 'distributor_id');
```

### Encrypted Storage

**Data Encryption at Rest:**
- Sensitive message content encrypted using `encryption_keys` table
- Customer PII automatically encrypted before storage
- AI responses containing sensitive data encrypted
- Encryption keys rotated regularly per distributor

**Encryption Implementation:**
```python
# Example encryption for sensitive message content
from cryptography.fernet import Fernet
import os

async def encrypt_message_content(content: str, distributor_id: str) -> str:
    """Encrypt message content using distributor-specific key"""
    # Retrieve encryption key for distributor
    key = await get_distributor_encryption_key(distributor_id)
    fernet = Fernet(key)
    
    # Encrypt content
    encrypted_content = fernet.encrypt(content.encode())
    return encrypted_content.decode()

async def decrypt_message_content(encrypted_content: str, distributor_id: str) -> str:
    """Decrypt message content using distributor-specific key"""
    key = await get_distributor_encryption_key(distributor_id)
    fernet = Fernet(key)
    
    # Decrypt content
    decrypted_content = fernet.decrypt(encrypted_content.encode())
    return decrypted_content.decode()
```

### PII Detection and Protection

**Automatic PII Detection:**
- Incoming messages scanned for personally identifiable information
- PII automatically flagged and stored in `pii_detection_results` table
- Sensitive data masked or encrypted before AI processing
- Compliance with GDPR, CCPA, and other privacy regulations

**PII Detection Categories:**
- Email addresses
- Phone numbers  
- Social security numbers
- Credit card numbers
- Government IDs
- Physical addresses
- Medical information

```python
import re
from typing import List, Dict

class PIIDetector:
    """Detect and classify PII in message content"""
    
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        }
    
    async def detect_pii(self, content: str) -> Dict[str, List[str]]:
        """Detect PII in message content"""
        detected = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                detected[pii_type] = matches
                
        return detected
    
    async def mask_pii(self, content: str) -> str:
        """Mask PII in content for AI processing"""
        masked_content = content
        
        for pii_type, pattern in self.patterns.items():
            if pii_type == 'email':
                masked_content = re.sub(pattern, '[EMAIL_REDACTED]', masked_content)
            elif pii_type == 'phone':
                masked_content = re.sub(pattern, '[PHONE_REDACTED]', masked_content)
            # Add more masking rules as needed
                
        return masked_content
```

### Audit Trail

**Complete Access Logging:**
- All database access logged in `data_access_audit` table
- User actions, timestamps, and data accessed tracked
- Failed access attempts logged for security monitoring
- Audit logs retained for compliance requirements

**Audit Log Structure:**
```sql
CREATE TABLE data_access_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distributor_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## AI Data Security

### Data Minimization

**Selective Data Sharing:**
- Only necessary data sent to OpenAI API
- PII masked or removed before AI processing
- Customer data minimized to essential context only
- Full message history not shared unless required

**Data Filtering Example:**
```python
async def prepare_context_for_ai(message: Message, conversation: Conversation) -> str:
    """Prepare safe context for AI processing"""
    
    # Detect and mask PII
    pii_detector = PIIDetector()
    masked_content = await pii_detector.mask_pii(message.content)
    
    # Limit conversation history
    recent_messages = await get_recent_messages(
        conversation.id, 
        limit=10,  # Only last 10 messages
        exclude_pii=True
    )
    
    # Create safe context
    safe_context = {
        'current_message': masked_content,
        'recent_context': [msg.content for msg in recent_messages],
        'customer_id': conversation.customer_id,  # UUID only, no PII
        'channel': conversation.channel
    }
    
    return json.dumps(safe_context)
```

### AI Response Tracking

**Complete AI Interaction Logging:**
- All AI requests and responses logged in `ai_responses` table
- Token usage, costs, and confidence scores tracked
- Failed AI requests logged for debugging
- Human feedback captured for quality improvement

**Response Security Features:**
```python
async def log_ai_response(
    message_id: str,
    agent_type: str,
    response_content: str,
    distributor_id: str,
    tokens_used: int,
    confidence: float
) -> None:
    """Securely log AI response with metadata"""
    
    # Check for any PII in AI response
    pii_detector = PIIDetector()
    detected_pii = await pii_detector.detect_pii(response_content)
    
    if detected_pii:
        # Flag response for review
        await flag_ai_response_for_review(message_id, detected_pii)
        
        # Encrypt response if it contains PII
        encrypted_response = await encrypt_message_content(
            response_content, 
            distributor_id
        )
        response_content = encrypted_response
    
    # Log response
    await supabase.table('ai_responses').insert({
        'message_id': message_id,
        'agent_type': agent_type,
        'response_content': response_content,
        'tokens_used': tokens_used,
        'confidence': confidence,
        'distributor_id': distributor_id,
        'contains_pii': bool(detected_pii),
        'created_at': datetime.utcnow().isoformat()
    }).execute()
```

### Privacy Compliance

**GDPR & Privacy Rights:**
- Right to deletion: Complete data removal upon request
- Data portability: Export all user data in standard format  
- Access logs: Users can view all access to their data
- Consent management: Granular permissions for AI processing

**Data Retention Policies:**
```python
# Configurable data retention per distributor
RETENTION_POLICIES = {
    'messages': 730,  # 2 years
    'ai_responses': 365,  # 1 year
    'audit_logs': 2555,  # 7 years (compliance)
    'pii_detection': 90   # 3 months
}

async def cleanup_expired_data(distributor_id: str) -> None:
    """Remove data past retention period"""
    for table, days in RETENTION_POLICIES.items():
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        await supabase.table(table).delete().eq(
            'distributor_id', distributor_id
        ).lt('created_at', cutoff_date.isoformat()).execute()
```

## Authentication & Authorization

### Supabase Auth Integration

**Multi-Factor Authentication:**
- TOTP-based 2FA for admin users
- SMS-based verification for critical actions
- Biometric authentication support on mobile
- Session timeout and re-authentication

**Role-Based Access Control:**
```typescript
// User roles with granular permissions
export type UserRole = 'OWNER' | 'ADMIN' | 'MANAGER' | 'OPERATOR';

export interface UserPermissions {
  messages: {
    read: boolean;
    write: boolean;
    delete: boolean;
  };
  ai_features: {
    view_suggestions: boolean;
    approve_responses: boolean;
    configure_agents: boolean;
  };
  customers: {
    read: boolean;
    write: boolean;
    export: boolean;
  };
  orders: {
    read: boolean;
    create: boolean;
    confirm: boolean;
  };
}

// Permission matrix by role
const ROLE_PERMISSIONS: Record<UserRole, UserPermissions> = {
  OWNER: {
    messages: { read: true, write: true, delete: true },
    ai_features: { view_suggestions: true, approve_responses: true, configure_agents: true },
    customers: { read: true, write: true, export: true },
    orders: { read: true, create: true, confirm: true }
  },
  ADMIN: {
    messages: { read: true, write: true, delete: true },
    ai_features: { view_suggestions: true, approve_responses: true, configure_agents: false },
    customers: { read: true, write: true, export: true },
    orders: { read: true, create: true, confirm: true }
  },
  MANAGER: {
    messages: { read: true, write: true, delete: false },
    ai_features: { view_suggestions: true, approve_responses: false, configure_agents: false },
    customers: { read: true, write: true, export: false },
    orders: { read: true, create: true, confirm: true }
  },
  OPERATOR: {
    messages: { read: true, write: true, delete: false },
    ai_features: { view_suggestions: true, approve_responses: false, configure_agents: false },
    customers: { read: true, write: false, export: false },
    orders: { read: true, create: false, confirm: false }
  }
};
```

### Session Management

**Secure Session Handling:**
- JWT tokens with short expiration times
- Refresh token rotation
- Device tracking and management
- Suspicious activity detection

```python
from datetime import datetime, timedelta
import jwt

class SessionManager:
    """Secure session management"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.access_token_expire = timedelta(minutes=15)
        self.refresh_token_expire = timedelta(days=7)
    
    async def create_session(self, user_id: str, distributor_id: str, role: str) -> Dict[str, str]:
        """Create secure session tokens"""
        
        # Access token payload
        access_payload = {
            'user_id': user_id,
            'distributor_id': distributor_id,
            'role': role,
            'exp': datetime.utcnow() + self.access_token_expire,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        # Refresh token payload  
        refresh_payload = {
            'user_id': user_id,
            'distributor_id': distributor_id,
            'exp': datetime.utcnow() + self.refresh_token_expire,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm='HS256')
        
        # Store session in database
        await self.store_session(user_id, refresh_token)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': self.access_token_expire.total_seconds()
        }
    
    async def validate_session(self, token: str) -> Dict[str, any]:
        """Validate session token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if session is still valid in database
            if payload['type'] == 'refresh':
                session_valid = await self.check_session_validity(
                    payload['user_id'], 
                    token
                )
                if not session_valid:
                    raise jwt.InvalidTokenError("Session revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise Exception("Token expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
```

## API Security

### JWT Authentication

**Token-Based Security:**
- All API endpoints protected with JWT authentication
- Distributor context automatically injected from token
- Token expiration and refresh mechanisms
- Invalid token handling and logging

### Rate Limiting

**API Request Throttling:**
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Rate limiting by distributor
@app.post("/api/messages")
@limiter.limit("100/minute")  # 100 requests per minute per distributor
async def create_message(
    request: Request,
    message_data: MessageCreate,
    distributor_id: str = Depends(get_current_distributor)
):
    """Create new message with rate limiting"""
    pass

# AI endpoint rate limiting (more restrictive)
@app.post("/api/ai/analyze")
@limiter.limit("50/minute")  # 50 AI requests per minute
async def analyze_message(
    request: Request,
    message_id: str,
    distributor_id: str = Depends(get_current_distributor)
):
    """Analyze message with AI (rate limited)"""
    pass
```

### CORS Configuration

**Cross-Origin Security:**
```python
from fastapi.middleware.cors import CORSMiddleware

# Production CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"]
)
```

### Input Validation

**Comprehensive Data Validation:**
```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional
import re

class MessageCreate(BaseModel):
    """Secure message creation model"""
    content: str
    conversation_id: str
    message_type: str = 'TEXT'
    attachments: Optional[List[str]] = []
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message content cannot be empty')
        if len(v) > 10000:  # 10KB limit
            raise ValueError('Message content too long')
        return v.strip()
    
    @validator('message_type')
    def validate_message_type(cls, v):
        allowed_types = ['TEXT', 'IMAGE', 'AUDIO', 'FILE', 'ORDER_CONTEXT']
        if v not in allowed_types:
            raise ValueError(f'Invalid message type. Must be one of: {allowed_types}')
        return v
    
    @validator('attachments')
    def validate_attachments(cls, v):
        if v and len(v) > 10:  # Max 10 attachments
            raise ValueError('Too many attachments')
        for attachment in v or []:
            if not attachment.startswith(('http://', 'https://')):
                raise ValueError('Invalid attachment URL')
        return v
```

## Webhook Security

### Signed Webhooks

**Cryptographic Verification:**
```python
import hmac
import hashlib
from fastapi import HTTPException

async def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify webhook signature"""
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )

@app.post("/webhook/whatsapp")
async def handle_whatsapp_webhook(
    request: Request,
    x_hub_signature: str = Header(None)
):
    """Handle WhatsApp webhook with signature verification"""
    
    body = await request.body()
    secret = os.getenv('WHATSAPP_WEBHOOK_SECRET')
    
    # Verify signature
    if not await verify_webhook_signature(body, x_hub_signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    data = await request.json()
    await process_whatsapp_message(data)
```

### Retry Logic

**Secure Retry Mechanisms:**
```python
import asyncio
from typing import Dict, Any

class WebhookRetryManager:
    """Secure webhook retry with exponential backoff"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 60  # seconds
    
    async def retry_webhook_delivery(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        distributor_id: str
    ) -> bool:
        """Retry webhook delivery with backoff"""
        
        for attempt in range(self.max_retries + 1):
            try:
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                if attempt > 0:
                    await asyncio.sleep(delay)
                
                # Attempt delivery
                success = await self.deliver_webhook(
                    webhook_url, 
                    payload, 
                    headers,
                    distributor_id
                )
                
                if success:
                    return True
                    
            except Exception as e:
                # Log delivery failure
                await self.log_webhook_failure(
                    webhook_url,
                    payload,
                    attempt,
                    str(e),
                    distributor_id
                )
        
        # All retries failed
        return False
```

### Endpoint Validation

**Webhook Endpoint Security:**
```python
async def validate_webhook_endpoint(url: str) -> bool:
    """Validate webhook endpoint security"""
    
    # Must use HTTPS
    if not url.startswith('https://'):
        return False
    
    # Check if endpoint is reachable
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=5)
            return response.status_code in [200, 404, 405]  # Endpoint exists
    except:
        return False

async def register_webhook(
    distributor_id: str,
    webhook_url: str,
    events: List[str]
) -> bool:
    """Register webhook with security validation"""
    
    # Validate endpoint
    if not await validate_webhook_endpoint(webhook_url):
        raise ValueError("Invalid or unreachable webhook endpoint")
    
    # Store webhook configuration
    await supabase.table('webhook_endpoints').insert({
        'distributor_id': distributor_id,
        'url': webhook_url,
        'events': events,
        'active': True,
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return True
```

## Security Monitoring

### Threat Detection

**Automated Security Monitoring:**
```python
class SecurityMonitor:
    """Real-time security threat detection"""
    
    async def detect_suspicious_activity(
        self,
        user_id: str,
        action: str,
        ip_address: str,
        user_agent: str
    ) -> bool:
        """Detect suspicious user activity"""
        
        # Check for rapid requests from same IP
        recent_requests = await self.get_recent_requests(ip_address, minutes=5)
        if len(recent_requests) > 100:  # More than 100 requests in 5 minutes
            await self.flag_suspicious_ip(ip_address)
            return True
        
        # Check for login from new location
        if action == 'login':
            known_locations = await self.get_user_known_locations(user_id)
            current_location = await self.get_ip_location(ip_address)
            
            if current_location not in known_locations:
                await self.send_location_alert(user_id, current_location)
        
        # Check for unusual user agent
        if await self.is_suspicious_user_agent(user_agent):
            await self.flag_suspicious_user_agent(user_id, user_agent)
            return True
        
        return False
    
    async def handle_security_incident(
        self,
        incident_type: str,
        details: Dict[str, Any],
        severity: str = 'medium'
    ) -> None:
        """Handle detected security incidents"""
        
        # Log incident
        await supabase.table('security_incidents').insert({
            'incident_type': incident_type,
            'details': details,
            'severity': severity,
            'status': 'open',
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        # Send alerts for high severity incidents
        if severity == 'high':
            await self.send_security_alert(incident_type, details)
        
        # Auto-remediation for certain incident types
        if incident_type == 'suspicious_ip':
            await self.temporarily_block_ip(details['ip_address'])
```

### Compliance Monitoring

**Regulatory Compliance Tracking:**
```python
class ComplianceMonitor:
    """Monitor and ensure regulatory compliance"""
    
    async def generate_compliance_report(
        self,
        distributor_id: str,
        report_type: str = 'gdpr'
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        
        if report_type == 'gdpr':
            return await self.generate_gdpr_report(distributor_id)
        elif report_type == 'ccpa':
            return await self.generate_ccpa_report(distributor_id)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    async def generate_gdpr_report(self, distributor_id: str) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        
        # Data processing activities
        message_count = await self.count_messages(distributor_id)
        ai_processing_count = await self.count_ai_responses(distributor_id)
        pii_detections = await self.count_pii_detections(distributor_id)
        
        # Data retention compliance
        retention_status = await self.check_retention_compliance(distributor_id)
        
        # User rights fulfillment
        deletion_requests = await self.count_deletion_requests(distributor_id)
        access_requests = await self.count_access_requests(distributor_id)
        
        return {
            'distributor_id': distributor_id,
            'report_date': datetime.utcnow().isoformat(),
            'data_processing': {
                'messages_processed': message_count,
                'ai_responses_generated': ai_processing_count,
                'pii_detections': pii_detections
            },
            'data_retention': retention_status,
            'user_rights': {
                'deletion_requests_fulfilled': deletion_requests,
                'access_requests_fulfilled': access_requests
            },
            'compliance_status': 'compliant'  # or 'non_compliant' with issues
        }
```

## Security Best Practices

### Development Security

**Secure Development Guidelines:**

1. **Never commit secrets to version control**
2. **Use environment variables for all sensitive configuration**
3. **Implement proper error handling without information disclosure**
4. **Regular dependency updates and vulnerability scanning**
5. **Code reviews with security focus**
6. **Automated security testing in CI/CD pipeline**

### Production Security

**Production Security Checklist:**

- [ ] All environment variables properly configured
- [ ] HTTPS enabled for all endpoints
- [ ] Database RLS policies active and tested
- [ ] JWT secrets are strong and rotated regularly
- [ ] API rate limiting configured
- [ ] Webhook signatures validated
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Regular security audits and penetration testing
- [ ] Incident response plan documented
- [ ] Staff security training completed

### Ongoing Security Maintenance

**Regular Security Tasks:**

1. **Weekly**: Review security logs and alerts
2. **Monthly**: Update dependencies and security patches
3. **Quarterly**: Rotate encryption keys and JWT secrets
4. **Annually**: Complete security audit and penetration testing
5. **As needed**: Respond to security incidents and vulnerabilities

**Security Metrics to Monitor:**

- Failed authentication attempts
- Suspicious IP activity
- PII detection rates
- AI response security flags
- Data retention compliance
- User permission changes
- Webhook delivery failures
- Database access patterns