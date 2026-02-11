"""Production runner for Dash dashboard.

Usage:
	python run_dashboard.py
"""

import os

from waitress import serve

from src.service.salary_dashboard import server


if __name__ == "__main__":
	host = os.getenv("DASH_HOST", "0.0.0.0")
	port = int(os.getenv("DASH_PORT", "8006"))
	threads = int(os.getenv("DASH_THREADS", "4"))
	serve(server, host=host, port=port, threads=threads)
