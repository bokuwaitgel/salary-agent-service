"""API runner for email service.

Usage:
	python run_api.py
"""

import os

import uvicorn


def main() -> None:
	host = os.getenv("API_HOST", "0.0.0.0")
	port = int(os.getenv("API_PORT", "8007"))
	workers = int(os.getenv("API_WORKERS", "1"))
	log_level = os.getenv("API_LOG_LEVEL", "info")
	proxy_headers = os.getenv("API_PROXY_HEADERS", "true").lower() in {"true", "1", "yes"}
	uvicorn.run(
		"src.api.email_app:app",
		host=host,
		port=port,
		reload=False,
		workers=workers,
		log_level=log_level,
		proxy_headers=proxy_headers,
	)


if __name__ == "__main__":
	main()
