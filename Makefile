load:
	python src/etl/loader.py

test:
	pytest

report:
	python src/report.py

clean:
	rm -rf __pycache__