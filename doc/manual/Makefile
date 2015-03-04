TEXFILE=manual.tex

compile:
	 mkdir -p tikz
	 latexmk -pdf -shell-escape -verbose ${TEXFILE}

all: clean compile

clean:
	mkdir -p tikz
	latexmk -C
	rm -f *.aux *.toc *.log
	rm -f tikz/*

aco:
	latexmk -verbose -shell-escape -pdf -pvc -silent ${TEXFILE}
