"""Set required environment variables before paperclip_mcp is imported."""
import os

os.environ.setdefault("PAPERCLIP_COMPANY_ID", "test-company-id")
os.environ.setdefault("PAPERCLIP_API_KEY", "test-api-key")
os.environ.setdefault("PAPERCLIP_BASE_URL", "http://localhost:3100/api")
