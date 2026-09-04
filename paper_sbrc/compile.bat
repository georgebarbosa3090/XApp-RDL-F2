@echo off
echo =======================================================
echo Compilando Artigo SBRC (xApp-RDL) em LaTeX...
echo =======================================================

pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

if exist main.pdf (
    echo.
    echo =======================================================
    echo [SUCESSO] Artigo compilado com sucesso: main.pdf
    echo =======================================================
) else (
    echo.
    echo =======================================================
    echo [AVISO] pdflatex nao encontrado ou erro na compilacao.
    echo Voce tambem pode enviar esta pasta diretamente ao Overleaf!
    echo =======================================================
)
