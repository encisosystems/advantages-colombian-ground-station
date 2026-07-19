FMT ?= png

.PHONY: all install figures figure-01 figure-02 figure-03 figure-04 figure-05 figure-06 simulation clean help

all: figures

help:
	@echo "Usage: make [target] [FMT=png|svg|eps]"
	@echo ""
	@echo "Targets:"
	@echo "  all          Build all figures (default)"
	@echo "  figures      Run all figure scripts via run_all.py"
	@echo "  figure-01    Ground station visibility map"
	@echo "  figure-02    Pass duration vs elevation mask"
	@echo "  figure-03    Ka-band atmospheric attenuation"
	@echo "  figure-04    Doppler shift profile"
	@echo "  figure-05    Coverage map"
	@echo "  figure-06    Cross-platform validation"
	@echo "  simulation   First-pass tracking geometry"
	@echo "  install      Install Python/conda dependencies"
	@echo "  clean        Remove all generated figure files"
	@echo ""
	@echo "Variables:"
	@echo "  FMT          Output format: png (default), svg, eps"
	@echo "               Example: make figures FMT=svg"

install:
	conda install -y -c conda-forge cartopy
	pip install -r requirements.txt

figures:
	FIGURE_FORMAT=$(FMT) python run_all.py

figure-01:
	FIGURE_FORMAT=$(FMT) python figure-01.py

figure-02:
	FIGURE_FORMAT=$(FMT) python figure-02.py

figure-03:
	FIGURE_FORMAT=$(FMT) python figure-03.py

figure-04:
	FIGURE_FORMAT=$(FMT) python figure-04.py

figure-05:
	FIGURE_FORMAT=$(FMT) python figure-05.py

figure-06:
	FIGURE_FORMAT=$(FMT) python figure-06.py

simulation:
	FIGURE_FORMAT=$(FMT) python simulation.py

clean:
	rm -f figure-01.png figure-01.svg figure-01.eps \
	      figure-02.png figure-02.svg figure-02.eps \
	      figure-03.png figure-03.svg figure-03.eps \
	      figure-04.png figure-04.svg figure-04.eps \
	      figure-05.png figure-05.svg figure-05.eps \
	      figure-06.png figure-06.svg figure-06.eps \
	      simulation.png simulation.svg simulation.eps
