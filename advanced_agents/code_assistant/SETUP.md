# Code Assistant Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Google API key for Gemini models

### 1. Clone and Navigate
```bash
git clone https://github.com/bitphonix/ai-agents-hub.git
cd ai-agents-hub/advanced_agents/code_assistant
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv code-assistant-env

# Activate virtual environment
# Windows:
code-assistant-env\Scripts\activate
# macOS/Linux:
source code-assistant-env/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your API key
# Add your Google API key:
GOOGLE_API_KEY=your_google_api_key_here
```

### 5. Initialize Vector Store
```bash
# Run document loader to create vector store
python document_loader.py
```

This will create:
- `vector_store/index.faiss` - Vector index
- `vector_store/index.pkl` - Metadata pickle file

### 6. Test the Setup
```bash
# Test the code assistant
python main.py --help

# Interactive mode
python main.py --interactive

# Generate code example
python main.py --generate "Create a function to calculate fibonacci numbers"
```

## 🔧 Development Setup

### Environment Variables
Create a `.env` file with:
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional Configuration
MODEL_NAME=gemini-1.5-flash
CODE_GENERATION_MODEL=gemini-1.5-pro
MAX_TOKENS=2000
TEMPERATURE=0.1
LOG_LEVEL=INFO
```

### Project Structure
```
code_assistant/
├── main.py                 # Main application entry point
├── code_generator.py       # Code generation engine
├── document_loader.py      # RAG system
├── validators.py          # Code validation and execution
├── config.py              # Configuration management
├── requirements.txt       # Dependencies
├── .env                   # Environment variables (you create this)
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── code-assistant-env/    # Virtual environment (auto-created)
├── vector_store/         # Vector embeddings (auto-created)
│   ├── index.faiss       # FAISS index (auto-generated)
│   └── index.pkl         # Metadata (auto-generated)
├── docs/                 # Documentation files
│   ├── *.txt            # Knowledge base files
│   └── *.md             # Setup guides
└── tests/               # Unit tests
    └── test_main.py     # Test suite
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_main.py -v

# Test with coverage
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

### Manual Testing
```bash
# Test code generator
python code_generator.py

# Test document loader
python document_loader.py

# Test validators
python validators.py
```

## 🔒 Security Notes

### Protected Files (.gitignore)
- `.env` - Contains API keys
- `config.py` - May contain sensitive configuration
- `vector_store/*.faiss` - Generated vector indices
- `vector_store/*.pkl` - Generated metadata
- `code-assistant-env/` - Virtual environment

### API Key Security
- Never commit `.env` files
- Use environment variables in production
- Rotate API keys regularly
- Use `.env.example` for templates

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Make sure virtual environment is activated
code-assistant-env\Scripts\activate  # Windows
source code-assistant-env/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### API Key Issues
```bash
# Check if API key is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key loaded:', bool(os.getenv('GOOGLE_API_KEY')))"
```

#### Vector Store Issues
```bash
# Rebuild vector store
rm -rf vector_store/  # Remove existing
python document_loader.py  # Rebuild
```

#### Permission Issues (Windows)
```bash
# If PowerShell execution policy blocks activation
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📚 Usage Examples

### Command Line Interface
```bash
# Interactive mode
python main.py --interactive

# Generate specific code
python main.py --generate "Create a REST API with FastAPI"

# Analyze code file
python main.py --analyze example.py

# Generate documentation
python main.py --document my_script.py
```

### Python API
```python
from main import CodeAssistantAgent

# Initialize agent
agent = CodeAssistantAgent()

# Generate code
result = agent.process_request("Create a data visualization function")
print(result.code_solution.code)
```

## 🚀 Production Deployment

### Environment Setup
1. Use production `.env` file
2. Set `LOG_LEVEL=WARNING`
3. Use production models (`gemini-1.5-pro`)
4. Enable rate limiting

### Performance Optimization
1. Pre-build vector store
2. Use faster embedding models for dev
3. Implement caching for repeated queries
4. Monitor API usage and costs

## 📖 Next Steps

1. **Extend Knowledge Base**: Add more documentation files to `docs/`
2. **Custom Models**: Integrate other LLM providers
3. **Web Interface**: Add FastAPI/Streamlit frontend
4. **CI/CD**: Set up automated testing and deployment
5. **Monitoring**: Add logging and performance metrics
