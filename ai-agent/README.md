# Order Agent - AI-Powered Customer Message Processing

A Python-based AI agent system that processes customer messages from multiple channels (WhatsApp, SMS, Email), classifies intent, extracts order details, and creates structured orders for B2B food distributors.

## 🏗️ Architecture

The Order Agent follows a **6-step workflow**:

1. **Message Analysis** - Classify customer intent (BUY, QUESTION, COMPLAINT, FOLLOW_UP, OTHER)
2. **Intent Classification** - Determine appropriate response pathway  
3. **Product Extraction** - Extract product names, quantities, and units from natural language
4. **Product Validation** - Match customer requests to product catalog using fuzzy matching
5. **Order Creation** - Create structured orders in database with "PENDIENTE" status
6. **Message Update** - Store AI analysis results for tracking and review

## 📁 Project Structure

```
ai-agent/
├── agents/           # Core AI agent implementation
│   ├── order_agent.py    # Main Pydantic AI agent
│   ├── prompts.py        # System prompts and templates
│   └── tools.py          # Agent tool functions
├── schemas/          # Pydantic data models
│   ├── message.py        # Message analysis models
│   ├── order.py          # Order creation models
│   └── product.py        # Product matching models
├── tools/            # Business logic utilities
│   ├── product_matcher.py   # Fuzzy product matching
│   └── supabase_tools.py    # Database operations
├── services/         # Service layer
│   └── database.py       # Database service with multi-tenant support
├── config/           # Configuration
│   └── settings.py       # Environment variables and settings
├── tests/            # Unit tests
│   ├── test_config.py
│   ├── test_schemas.py
│   ├── test_product_matcher.py
│   └── test_integration.py
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- OpenAI API key
- Supabase project with database schema

### Installation

1. **Create virtual environment**:
   ```bash
   cd ai-agent
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   DEMO_DISTRIBUTOR_ID=your_distributor_id
   ```

4. **Run the agent**:
   ```bash
   python main.py
   ```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Coverage

- **Configuration**: Environment variable loading and validation
- **Schemas**: Pydantic model validation and serialization
- **Product Matcher**: Fuzzy matching algorithms and confidence scoring  
- **Integration**: End-to-end workflow testing

## 🔧 Configuration

Key configuration options in `config/settings.py`:

- `OPENAI_MODEL`: AI model to use (default: "gpt-4")
- `BATCH_SIZE`: Messages to process per batch (default: 10)
- `AI_CONFIDENCE_THRESHOLD`: Minimum confidence for auto-processing (default: 0.8)
- `MAX_RETRIES`: Maximum retry attempts for AI calls (default: 3)

## 🏢 Multi-Tenant Architecture

The system supports multiple distributors with:
- **Row Level Security (RLS)** enforcement
- **Distributor ID filtering** on all database operations
- **Isolated product catalogs** per distributor
- **Separate confidence thresholds** per distributor

## 📊 Monitoring & Logging

- **Structured logging** with configurable levels
- **Processing time tracking** for performance monitoring
- **Confidence score logging** for quality assessment
- **Error tracking** with retry mechanisms

## 🔗 Integration

The agent integrates with the main application via:

- **Database**: Supabase with shared schema
- **API calls**: Frontend calls agent endpoints
- **Message queues**: Processes unread messages from database
- **Webhooks**: Receives messages from Twilio/WhatsApp

## 🛡️ Security

- **Environment variable protection** for API keys
- **Input validation** using Pydantic models
- **SQL injection prevention** via parameterized queries
- **Multi-tenant isolation** with distributor filtering
- **Rate limiting** and retry logic for external APIs

## 📈 Performance

- **Async processing** for concurrent message handling
- **Batch processing** to optimize database operations
- **Connection pooling** for database efficiency
- **Caching** for product catalog lookups
- **Graceful shutdown** handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is part of the Order Agent system for B2B food distributors.