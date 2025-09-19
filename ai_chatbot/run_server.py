"""
Startup script for the AI Chatbot API
Run this from the project root directory
"""
import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the FastAPI application"""
    try:
        host = os.getenv('HOST', '127.0.0.1')
        port = int(os.getenv('PORT', 8001))
        
        print(f"🚀 Starting AI Chatbot API on {host}:{port}")
        print("📊 Features enabled:")
        print("  - Groq LLM integration")
        print("  - TiDB vector store")
        print("  - Knowledge base with sample data")
        print("  - Chat history tracking")
        print("  - Meeting processing endpoints")
        print("\n📖 API Documentation available at:")
        print(f"  - Swagger UI: http://{host}:{port}/docs")
        print(f"  - ReDoc: http://{host}:{port}/redoc")
        print(f"\n🔧 Starting server from app.main...")
        
        # Since your main.py is in the app/ directory, we need to use app.main
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,
            log_level=os.getenv('LOG_LEVEL', 'info').lower()
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print("Make sure you're running this from the project root directory")
        sys.exit(1)

if __name__ == "__main__":
    main()