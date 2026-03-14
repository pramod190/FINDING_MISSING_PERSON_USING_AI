install:
	pip install -r requirements.txt

run_desktop:
	streamlit run Home.py --server.port 8501

run_mobile:
	streamlit run mobile_app.py --server.port 8502

run_all:
	streamlit run Home.py --server.port 8501 & streamlit run mobile_app.py --server.port 8502

generate_passwords:
	python generate_passwords.py

clean:
	rm -f sqlite_database.db
	rm -rf resources/*.jpg resources/*.jpeg resources/*.png
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
