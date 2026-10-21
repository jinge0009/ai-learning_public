from pathlib import Path
from pypdf import PdfReader
from docx import Document

def load_pdf(file_path: str) -> str:
    """读 PDF，返回纯文本"""
    reader = PdfReader(file_path)
    pages = []
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            pages.append(f"--- 第 {page_num} 页 ---\n{text}")
    return "\n\n".join(pages)

def load_docx(file_path: str) -> str:
    """读 Word，返回纯文本"""
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

def load_document(file_path: str) -> str:
    """统一入口，根据扩展名加载"""
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


def analyze_document(file_path: str) -> dict:
    """统计文档信息"""
    text = load_document(file_path)
    return {
        "file_name": Path(file_path).name,
        "total_chars": len(text),
        "total_lines": len(text.splitlines()),
        "total_words": len(text.split()),
        "preview": text[:100]
    }

if __name__ == "__main__":
    files = ["sample.pdf"]    # 改成你的文件名

    for f in files:
        try:
            print(analyze_document(f))
        except FileNotFoundError:
            print(f"✗ {f}: 文件不存在")
        except Exception as e:
            print(f"✗ {f}: {e}")