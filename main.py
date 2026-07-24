"""
RAG-ALL: Main Entry Point
AI-Agent hỗ trợ nghiên cứu, học tập, làm luận án, luận văn.
"""

import sys


def main():
    """Main entry point for RAG-ALL CLI."""
    print("🚀 RAG-ALL - AI-Agent Research Assistant")
    print("=" * 50)
    print()
    print("Available commands:")
    print("  rag-all          - Start interactive CLI")
    print("  rag-all --help   - Show help")
    print()
    print("Services:")
    print("  Gateway:      http://localhost:8000")
    print("  WebUI:        http://localhost:8005")
    print("  API Docs:     http://localhost:8000/docs")
    print()
    print("For more information, see README.md")
    print()


if __name__ == "__main__":
    main()
