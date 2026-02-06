"""
Flatten salary analysis JSON files into CSV and save to database.
"""
import json
import csv
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class JobCategorySalary(Base):
    """Job Category Salary Analysis Table"""
    __tablename__ = "job_category_salary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_category = Column(String(255), nullable=False)
    min_salary = Column(Float)
    max_salary = Column(Float)
    average_salary = Column(Float)
    requirements_details = Column(Text)
    bonus_details = Column(Text)
    job_count = Column(Integer)
    source_zangia = Column(Integer)
    source_lambda = Column(Integer)
    month = Column(Integer, default=datetime.now().month)
    year = Column(Integer, default=datetime.now().year)
    created_at = Column(DateTime, default=datetime.now)


class JobCategoryRequirement(Base):
    """Job Category Requirements Table (Normalized)"""
    __tablename__ = "job_category_requirement"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_category = Column(String(255), nullable=False)
    requirement_name = Column(String(255))
    requirement_details = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class JobCategoryBonus(Base):
    """Job Category Bonus Table (Normalized)"""
    __tablename__ = "job_category_bonus"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_category = Column(String(255), nullable=False)
    bonus_name = Column(String(255))
    bonus_description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class JobLevelSalary(Base):
    """Job Level Salary Analysis Table"""
    __tablename__ = "job_level_salary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_level = Column(String(255), nullable=False)
    min_salary = Column(Float)
    max_salary = Column(Float)
    average_salary = Column(Float)
    requirements_details = Column(Text)
    bonus_details = Column(Text)
    job_count = Column(Integer)
    source_zangia = Column(Integer)
    source_lambda = Column(Integer)
    month = Column(Integer, default=datetime.now().month)
    year = Column(Integer, default=datetime.now().year)
    created_at = Column(DateTime, default=datetime.now)


class JobLevelRequirement(Base):
    """Job Level Requirements Table (Normalized)"""
    __tablename__ = "job_level_requirement"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_level = Column(String(255), nullable=False)
    requirement_name = Column(String(255))
    requirement_details = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class JobLevelBonus(Base):
    """Job Level Bonus Table (Normalized)"""
    __tablename__ = "job_level_bonus"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_level = Column(String(255), nullable=False)
    bonus_name = Column(String(255))
    bonus_description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


def get_engine():
    """Create database engine"""
    conn_str = os.getenv("DATABASE_URI", "sqlite:///products.db")
    return create_engine(conn_str, echo=True)


def flatten_to_csv(json_data, output_csv_file, data_type="category"):
    """
    Flatten nested JSON to CSV format
    """
    flattened_rows = []
    
    for key, value in json_data.items():
        # Main row
        row = {
            f"job_{data_type}": key,
            "min_salary": value.get("min_salary"),
            "max_salary": value.get("max_salary"),
            "average_salary": value.get("average_salary"),
            "requirements_details": value.get("requirements_details"),
            "bonus_details": value.get("bonus_details"),
            "job_count": value.get("job_count"),
            "source_zangia": value.get("source_counts", {}).get("Zangia", 0),
            "source_lambda": value.get("source_counts", {}).get("Lambda Global", 0),
        }
        
        # Flatten requirements
        requirements = value.get("requirements", [])
        for idx, req in enumerate(requirements):
            row[f"requirement_{idx+1}_name"] = req.get("name")
            row[f"requirement_{idx+1}_details"] = req.get("details")
        
        # Flatten bonuses
        bonuses = value.get("bonus", [])
        for idx, bonus in enumerate(bonuses):
            row[f"bonus_{idx+1}_name"] = bonus.get("name")
            row[f"bonus_{idx+1}_description"] = bonus.get("description")
        
        flattened_rows.append(row)
    
    # Write to CSV
    if flattened_rows:
        fieldnames = list(flattened_rows[0].keys())
        with open(output_csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_rows)
        print(f"✓ CSV saved to: {output_csv_file}")
    
    return flattened_rows


def save_to_database(json_data, data_type="category"):
    """
    Save flattened data to database with normalized structure
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        if data_type == "category":
            # Clear existing data
            session.query(JobCategorySalary).delete()
            session.query(JobCategoryRequirement).delete()
            session.query(JobCategoryBonus).delete()
            
            for job_category, data in json_data.items():
                # Insert main salary data
                salary_record = JobCategorySalary(
                    job_category=job_category,
                    min_salary=data.get("min_salary"),
                    max_salary=data.get("max_salary"),
                    average_salary=data.get("average_salary"),
                    requirements_details=data.get("requirements_details"),
                    bonus_details=data.get("bonus_details"),
                    job_count=data.get("job_count"),
                    source_zangia=data.get("source_counts", {}).get("Zangia", 0),
                    source_lambda=data.get("source_counts", {}).get("Lambda Global", 0)
                )
                session.add(salary_record)
                
                # Insert requirements
                for req in data.get("requirements", []):
                    req_record = JobCategoryRequirement(
                        job_category=job_category,
                        requirement_name=req.get("name"),
                        requirement_details=req.get("details")
                    )
                    session.add(req_record)
                
                # Insert bonuses
                for bonus in data.get("bonus", []):
                    bonus_record = JobCategoryBonus(
                        job_category=job_category,
                        bonus_name=bonus.get("name"),
                        bonus_description=bonus.get("description")
                    )
                    session.add(bonus_record)
        
        elif data_type == "level":
            # Clear existing data
            session.query(JobLevelSalary).delete()
            session.query(JobLevelRequirement).delete()
            session.query(JobLevelBonus).delete()
            
            for job_level, data in json_data.items():
                # Insert main salary data
                salary_record = JobLevelSalary(
                    job_level=job_level,
                    min_salary=data.get("min_salary"),
                    max_salary=data.get("max_salary"),
                    average_salary=data.get("average_salary"),
                    requirements_details=data.get("requirements_details"),
                    bonus_details=data.get("bonus_details"),
                    job_count=data.get("job_count"),
                    source_zangia=data.get("source_counts", {}).get("Zangia", 0),
                    source_lambda=data.get("source_counts", {}).get("Lambda Global", 0)
                )
                session.add(salary_record)
                
                # Insert requirements
                for req in data.get("requirements", []):
                    req_record = JobLevelRequirement(
                        job_level=job_level,
                        requirement_name=req.get("name"),
                        requirement_details=req.get("details")
                    )
                    session.add(req_record)
                
                # Insert bonuses
                for bonus in data.get("bonus", []):
                    bonus_record = JobLevelBonus(
                        job_level=job_level,
                        bonus_name=bonus.get("name"),
                        bonus_description=bonus.get("description")
                    )
                    session.add(bonus_record)
        
        session.commit()
        print(f"✓ Database updated successfully for {data_type} data")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error saving to database: {e}")
        raise
    finally:
        session.close()


def main():
    """Main execution function"""
    print("=" * 60)
    print("Flattening Salary Analysis Data")
    print("=" * 60)
    
    # Define file paths
    category_json = "outputs/job_category_salary_analysis_results.json"
    level_json = "outputs/job_level_salary_analysis_results.json"
    
    category_csv = "outputs/job_category_salary_flattened.csv"
    level_csv = "outputs/job_level_salary_flattened.csv"
    
    # Process Job Category Data
    print("\n[1/4] Processing Job Category data...")
    with open(category_json, 'r', encoding='utf-8') as f:
        category_data = json.load(f)
    
    print(f"  Found {len(category_data)} job categories")
    flatten_to_csv(category_data, category_csv, data_type="category")
    
    # Process Job Level Data
    print("\n[2/4] Processing Job Level data...")
    with open(level_json, 'r', encoding='utf-8') as f:
        level_data = json.load(f)
    
    print(f"  Found {len(level_data)} job levels")
    flatten_to_csv(level_data, level_csv, data_type="level")
    
    # Save to Database
    print("\n[3/4] Saving Job Category data to database...")
    save_to_database(category_data, data_type="category")
    
    print("\n[4/4] Saving Job Level data to database...")
    save_to_database(level_data, data_type="level")
    
    print("\n" + "=" * 60)
    print("✓ All operations completed successfully!")
    print("=" * 60)
    print("\nGenerated files:")
    print(f"  - {category_csv}")
    print(f"  - {level_csv}")
    print("\nDatabase tables created:")
    print("  - job_category_salary")
    print("  - job_category_requirement")
    print("  - job_category_bonus")
    print("  - job_level_salary")
    print("  - job_level_requirement")
    print("  - job_level_bonus")


if __name__ == "__main__":
    main()
