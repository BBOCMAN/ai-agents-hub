---
name: 🐛 Bug Report
about: Report a bug or issue with an AI agent
title: '[BUG] '
labels: ['bug', 'triage']
assignees: ''
---

## 🐛 Bug Description

### What happened?
<!-- A clear and concise description of what the bug is -->

### What did you expect to happen?
<!-- A clear and concise description of what you expected to happen -->

## 🎯 Affected Component

### Which agent/component is affected?
- [ ] 🧠 Advanced Code Assistant
- [ ] 🎮 Simple Agent: ________________
- [ ] 📓 Notebook: ________________
- [ ] 🔌 MCP Agent: ________________
- [ ] 🛠️ Infrastructure/CI
- [ ] 📚 Documentation
- [ ] Other: ________________

## 🔄 Steps to Reproduce

### Environment Setup
```bash
# Provide setup commands
pip install -r requirements.txt
cp .env.example .env
# etc.
```

### Reproduction Steps
1. 
2. 
3. 
4. 

### Minimal Code Example
```python
# Provide the minimal code that reproduces the issue
```

## 💻 Environment Information

### System Details
- **OS**: <!-- Windows 11, macOS 13, Ubuntu 22.04, etc. -->
- **Python Version**: <!-- 3.10.0, 3.11.2, etc. -->
- **Repository Version**: <!-- commit hash or release tag -->

### Dependencies
```bash
# Output of: pip list | grep -E "(langchain|langgraph|faiss|openai|google)"
```

### Configuration
- **LLM Provider**: <!-- OpenAI, Google Gemini, Anthropic, etc. -->
- **Vector Store**: <!-- FAISS, Chroma, Pinecone, etc. -->
- **Other relevant config**: 

## 📊 Error Details

### Error Messages
```
# Paste the full error message/stack trace here
```

### Logs
```
# Paste relevant log output here (remove any sensitive information)
```

### Screenshots
<!-- Add screenshots if they help explain the issue -->

## 🧪 Testing Information

### Does this happen consistently?
- [ ] Yes, always
- [ ] Sometimes (___% of the time)
- [ ] Only under specific conditions
- [ ] Unable to reproduce consistently

### When did this start happening?
- [ ] After recent update
- [ ] Fresh installation
- [ ] Has always been broken
- [ ] Unknown

### Workarounds
<!-- Any temporary fixes or workarounds you've found -->

## 🔍 Additional Investigation

### Related Issues
<!-- Link any related issues -->
- Related to #(issue number)
- Might be caused by #(issue number)

### Debugging Attempts
<!-- What you've already tried to fix this -->
- [ ] Reinstalled dependencies
- [ ] Cleared cache/temp files
- [ ] Checked environment variables
- [ ] Tested with different inputs
- [ ] Other: ________________

## 💡 Potential Causes
<!-- Your thoughts on what might be causing this -->

## 🎯 Impact Assessment

### Severity Level
- [ ] 🔥 **Critical** - Blocks core functionality
- [ ] 🚨 **High** - Major feature broken
- [ ] ⚠️ **Medium** - Feature partially works
- [ ] ℹ️ **Low** - Minor inconvenience

### Who is affected?
- [ ] All users
- [ ] Users of specific agent: ________________
- [ ] Users with specific setup: ________________
- [ ] Only me (so far)

---

### 🏷️ Labels for Maintainers
<!-- Maintainers: Add appropriate labels -->
- Priority: `low` | `medium` | `high` | `critical`
- Complexity: `beginner` | `intermediate` | `advanced`
- Component: `agent` | `infrastructure` | `documentation`
