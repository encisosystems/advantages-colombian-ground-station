.PHONY: all install figures figure-01 figure-02 figure-03 figure-04 figure-05 figure-06 simulation clean

all: figures

install:
	conda install -y -c conda-forge cartopy
	pip install -r requirements.txt

figures:
	python run_all.py

figure-01:
	python figure-01.py

figure-02:
	python figure-02.py

figure-03:
	python figure-03.py

figure-04:
	python figure-04.py

figure-05:
	python figure-05.py

figure-06:
	python figure-06.py

simulation:
	python simulation.py

clean:
	rm -f figure-01.png figure-02.png figure-03.png figure-04.png figure-05.png figure-06.png simulation.png
