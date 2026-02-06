"""Entry point for the salary analysis dashboard."""

from src.service.dashboard import app

if __name__ == "__main__":
    app.run(debug=True, port="8006")
