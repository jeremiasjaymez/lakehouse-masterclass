from rag_utils import build_document_chunks

if __name__ == "__main__":
    chunks = build_document_chunks()
    print("Chunks generados:", len(chunks))
    for chunk in chunks[:5]:
        print(chunk["source_path"], "::", chunk["section_title"])
