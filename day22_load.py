from pathlib import Path
from pypdf import PdfReader
from docx import Document

def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            pages.append(f"--- 第 {page_num} 页 ---\n{text}")
    return "\n\n".join(pages)

def load_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

def load_document(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(file_path)
    elif suffix == ".docx":
        return load_docx(file_path)
    elif suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"不支持的文件类型: {suffix}")

# ========== 运行测试 ==========
if __name__ == "__main__":
    # 换成你自己的文件名
    files = ["sample.txt"]    # 有 PDF 就写 "sample.pdf"
    
    for f in files:
        try:
            text = load_document(f)
            print(f"✓ {f}")
            print(f"  字符数: {len(text)}")
            print(f"  前200字: {text[:200]}")
            print()
        except FileNotFoundError:
            print(f"✗ {f}: 文件不存在")
        except Exception as e:
            print(f"✗ {f}: {e}")