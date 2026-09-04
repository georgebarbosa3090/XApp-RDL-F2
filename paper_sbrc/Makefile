# Makefile para compilação do artigo SBRC em LaTeX

MAIN = main
BIB = sbrc_references

all: pdf

pdf:
	pdflatex $(MAIN)
	bibtex $(MAIN)
	pdflatex $(MAIN)
	pdflatex $(MAIN)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk $(MAIN).pdf

.PHONY: all pdf clean
