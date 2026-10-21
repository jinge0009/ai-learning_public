def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """按字符数切分文本，带重叠"""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        # 尝试在句子边界切分
        if end < text_length:
            # 找最后一个句号、问号、感叹号、换行
            for sep in ["。", "！", "？", "\n", ".", "!", "?"]:
                last_sep = chunk.rfind(sep)
                if last_sep > chunk_size * 0.5:    # 至少过半才在这切
                    chunk = chunk[:last_sep + 1]
                    end = start + last_sep + 1
                    break

        chunks.append(chunk.strip())
        start = end - chunk_overlap    # 回退 overlap 个字符

    return [c for c in chunks if c]    # 过滤空块


if __name__ == "__main__":
    from day22_load import load_document

    text = load_document("sample.pdf")
    print(f"原文长度: {len(text)} 字符\n")

    chunks = split_text(text, chunk_size=200, chunk_overlap=30)
    print(f"切分成 {len(chunks)} 块\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"--- 块 {i} ({len(chunk)}字) ---")
        print(chunk)
        print()