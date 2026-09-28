import fitz
import os
import json

papers = {
    "2501.05879v1": r"C:\Users\george.barbosa\Downloads\UFPA\xApp RDL\2501.05879v1.pdf",
    "2605.24662v1": r"C:\Users\george.barbosa\Downloads\UFPA\xApp RDL\2605.24662v1.pdf",
    "Arquitetura_4": r"C:\Users\george.barbosa\Downloads\Arquitetura (4).pdf",
}

output_data = {}

for name, path in papers.items():
    if not os.path.exists(path):
        print(f"[ERRO] Arquivo nao encontrado: {path}")
        continue
    doc = fitz.open(path)
    text_full = ""
    pages_summary = []
    print(f"=== Processando {name}: {doc.page_count} paginas ===")
    for i in range(doc.page_count):
        page = doc.load_page(i)
        t = page.get_text()
        text_full += f"\n--- Page {i+1} ---\n" + t
        pages_summary.append({
            "page": i + 1,
            "char_count": len(t),
            "snippet": t[:300].replace("\n", " ")
        })
    output_data[name] = {
        "page_count": doc.page_count,
        "text": text_full,
        "pages": pages_summary
    }

# Save extracted text to local scratch
os.makedirs("scratch/extracted_papers", exist_ok=True)
for name, data in output_data.items():
    with open(f"scratch/extracted_papers/{name}.txt", "w", encoding="utf-8") as f:
        f.write(data["text"])
    print(f"[OK] Salvo scratch/extracted_papers/{name}.txt ({len(data['text'])} caracteres)")

print("Extração concluída!")
