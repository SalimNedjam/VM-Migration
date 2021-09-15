all: report

report: report.tex
	pdflatex report
	bibtex report
	pdflatex report
	pdflatex report

	

clean:
	rm -f *.aux *.log *.bbl *.blg *.toc *.dvi *.synctex.gz *.fls *.fdb_latexmk
