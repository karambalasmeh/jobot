from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(
    documents: List[Document], 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200
) -> List[Document]:
    """
    تقطيع النصوص لفقرات أصغر مع الحفاظ على السياق (Overlap).
    يدعم الفواصل الإنجليزية والعربية.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=[
            "\n\n", 
            "\n", 
            " ", 
            ".", 
            "؟", # علامة الاستفهام العربية
            "،", # الفاصلة العربية
            ""
        ],
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_documents(documents)
    
    # تنظيف الفراغات الزائدة والأسطر الفارغة داخل كل قطعة (اختياري لكنه يرفع الجودة)
    for chunk in chunks:
        chunk.page_content = " ".join(chunk.page_content.split())
        
    return chunks

# لاختبار الملف بشكل مستقل
if __name__ == "__main__":
    # مثال وهمي للاختبار
    from langchain_core.documents import Document
    sample_docs = [Document(page_content="This is a test document. " * 50, metadata={"source": "test.pdf"})]
    chunks = split_documents(sample_docs)
    print(f"Created {len(chunks)} chunks.")