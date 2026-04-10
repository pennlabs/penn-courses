#!/usr/bin/env python
"""
Interactive RAG test script - test different queries easily

Usage:
    export DATABASE_URL=postgres://penn-courses:postgres@localhost:5432/postgres
    uv run python test_rag_interactive.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PennCourses.settings.development')

import django
django.setup()

from review.views import retrieve_courses, call_llm

def test_query(query):
    """Test a single query"""
    print("\n" + "="*70)
    print(f"QUERY: \"{query}\"")
    print("="*70)
    
    # Step 1: Retrieve courses using RAG
    print("\n1. Retrieving relevant courses...")
    docs = retrieve_courses(query, top_k=10)
    print(f"✓ Found {len(docs)} documents\n")
    
    if docs:
        print("Top courses found:")
        for i, doc in enumerate(docs[:10], 1):
            code = doc.get('course_code', 'N/A')
            sim = doc.get('similarity', 0)
            text_preview = doc.get('text', '')[:60]
            print(f"  {i:2d}. {code:12s} (similarity: {sim:.4f}) - {text_preview}...")
    else:
        print("⚠ No documents found")
        return
    
    # Step 2: Call LLM (which internally calls build_prompt)
    print("\n" + "-"*70)
    print("2. Calling LLM with retrieved context...")
    print("-"*70)
    
    response, citations = call_llm(query, history_msgs=[], top_k=10)
    
    print("\nLLM RESPONSE:")
    print("-"*70)
    print(response)
    if citations:
        print(f"\nCitations: {citations}")
    print("="*70)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("RAG Interactive Test")
    print("="*70)
    print("\nEnter queries to test (or 'quit' to exit)")
    print("\nExamples:")
    print("  - cs courses")
    print("  - What is CIS-120?")
    print("  - computer science programming courses")
    print("  - math courses")
    print("  - statistics courses")
    print("  - machine learning courses")
    print("\n" + "-"*70)
    
    while True:
        try:
            query = input("\nQuery: ").strip()
            if not query:
                continue
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            test_query(query)
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

