import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

import asyncio
from app.rag.retriever import retrieve_relevant_documents
from app.rag.generator import _format_docs
from app.core.config import settings

def test_query():
    query = "What are the exact operating hours and street addresses for Future Stations in Mafraq and Karak?"
    print(f"Testing Query: {query}")
    
    results = retrieve_relevant_documents(query)
    
    print("\n--- RETRIEVED RESULTS ---")
    for i, (doc, score) in enumerate(results):
        print(f"Doc {i+1} [Score: {score:.4f}]")
        print(f"Source: {doc.metadata.get('source_file')}")
        print(f"Content Preview: {doc.page_content[:200]}...")
        print("-" * 20)
    
    context = _format_docs([doc for doc, score in results])
    # print("\n--- FULL CONTEXT ---")
    # print(context)
    
    # Check if 'Mafraq' or 'Karak' or 'operating hours' appear in context
    found_mafraq = "Mafraq" in context or "المفرق" in context
    found_karak = "Karak" in context or "الكرك" in context
    found_hours = "hours" in context or "ساعات" in context or "ساعة" in context
    
    print(f"\nKeywords found in context:")
    print(f"Mafraq: {found_mafraq}")
    print(f"Karak: {found_karak}")
    print(f"Hours: {found_hours}")

if __name__ == "__main__":
    test_query()
