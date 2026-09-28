import fitz
import os

pdf_list = {
    "2501.05879v1": r"C:\Users\george.barbosa\Downloads\UFPA\xApp RDL\2501.05879v1.pdf",
    "2605.24662v1": r"C:\Users\george.barbosa\Downloads\UFPA\xApp RDL\2605.24662v1.pdf",
    "Arquitetura_4": r"C:\Users\george.barbosa\Downloads\Arquitetura (4).pdf",
}

os.makedirs("scratch/extracted_images", exist_ok=True)

for name, path in pdf_list.items():
    if not os.path.exists(path):
        continue
    doc = fitz.open(path)
    img_count = 0
    for i, page in enumerate(doc):
        # Render whole page as image at 200 dpi for full visual layout understanding
        pix = page.get_pixmap(dpi=150)
        page_img_path = f"scratch/extracted_images/{name}_page_{i+1}.png"
        pix.save(page_img_path)
        print(f"Rendered: {page_img_path}")

        # Also extract embedded images
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            img_filename = f"scratch/extracted_images/{name}_p{i+1}_img{img_index+1}.{image_ext}"
            with open(img_filename, "wb") as f:
                f.write(image_bytes)
            img_count += 1
            print(f"  Extracted image: {img_filename}")

print("Imagens extraídas com sucesso!")
