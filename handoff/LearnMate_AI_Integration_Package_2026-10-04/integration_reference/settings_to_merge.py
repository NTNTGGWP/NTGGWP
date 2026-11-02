"""把这些设定合并到 Django settings.py；不要在这里写真实金钥。"""
import os

AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY', '')
AZURE_OPENAI_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT', '')
AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-01')

# ai_assistant.py 会优先选择 Azure；以下只有保留 fallback 时才需要。
AI_PROVIDER = os.environ.get('AI_PROVIDER', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.8-flash')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
AI_ASSISTANT_MODEL = os.environ.get('AI_ASSISTANT_MODEL', 'claude-opus-5')

