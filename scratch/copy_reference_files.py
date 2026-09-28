import shutil
import os
import glob

src_dirs = [
    r"C:\Users\george.barbosa\Downloads\paper H-RDL\figures",
    r"C:\Users\george.barbosa\Downloads\paper_CA-RDL\figures",
    r"C:\Users\george.barbosa\Downloads",
]

dest_dir = "scratch/reference_figures"
os.makedirs(dest_dir, exist_ok=True)

for sdir in src_dirs:
    if not os.path.exists(sdir):
        continue
    for ext in ["*.tex", "*.png", "*.pdf", "*.md"]:
        for f in glob.glob(os.path.join(sdir, ext)):
            base = os.path.basename(f)
            dest_path = os.path.join(dest_dir, base)
            try:
                shutil.copy2(f, dest_path)
                print(f"Copied: {base}")
            except Exception as e:
                print(f"Error copying {base}: {e}")

print("Arquivos de referência copiados com sucesso!")
