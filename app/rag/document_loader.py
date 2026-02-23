import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader

# تحديد مسار مجلد الداتا في جذر المشروع (خارج مجلد app لتجنب uvicorn reload)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

def load_documents(data_directory: Path | str = DEFAULT_DATA_DIR) -> List[Document]:
    """
    قراءة جميع ملفات الـ PDF من المجلد المحدد واستخراج النصوص والـ Metadata.
    """
    data_path = Path(data_directory)
    
    if not data_path.exists() or not data_path.is_dir():
        raise FileNotFoundError(f"Data directory not found or is not a directory: {data_path}")

    all_documents = []
    
    # البحث عن كل ملفات PDF في المجلد
    for file_path in data_path.glob("*.pdf"):
        # PyMuPDFLoader ممتاز في قراءة الجداول والنصوص المعقدة
        loader = PyMuPDFLoader(str(file_path))
        documents = loader.load()
        
        for doc in documents:
            # إضافة اسم الملف كـ Metadata لغايات التوثيق (Citations) لاحقاً
            doc.metadata["source_file"] = file_path.name
            
        all_documents.extend(documents)
        
    return all_documents

# لاختبار الملف بشكل مستقل
if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} pages from PDFs.")