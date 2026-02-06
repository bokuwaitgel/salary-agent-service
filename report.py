from dotenv import load_dotenv
load_dotenv()

from src.service.report import main as generate_report

if __name__ == "__main__":
    generate_report()