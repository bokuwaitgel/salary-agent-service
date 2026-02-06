import json
import pandas as pd
from pathlib import Path
from typing import Optional


class PaylabDataConverter:
    """Service to convert Paylab JSON data to CSV format"""
    
    def __init__(self, json_file_path: str = "results/paylab_job_data.json"):
        self.json_file_path = json_file_path
        
    def load_json_data(self) -> dict:
        """Load JSON data from file"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def convert_to_dataframe(self, data: dict) -> pd.DataFrame:
        """Convert JSON data to pandas DataFrame"""
        all_jobs = []
        
        for category in data['jobs_data']:
            category_name = category['category_name']
            category_min = category['min_salary']
            category_max = category['max_salary']
            
            for job in category['job_list']:
                all_jobs.append({
                    'category': category_name,
                    'category_min_salary': category_min,
                    'category_max_salary': category_max,
                    'job_title': job['job_title'],
                    'job_min_salary': job['min_salary'],
                    'job_max_salary': job['max_salary'],
                    'job_average_salary': (job['min_salary'] + job['max_salary']) / 2,
                    'salary_range': job['max_salary'] - job['min_salary'],
                    'job_url': job['job_url']
                })
        
        return pd.DataFrame(all_jobs)
    
    def get_category_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate summary statistics by category"""
        summary = df.groupby('category').agg({
            'job_title': 'count',
            'job_min_salary': ['min', 'mean', 'max'],
            'job_max_salary': ['min', 'mean', 'max'],
            'job_average_salary': 'mean',
            'salary_range': 'mean'
        }).round(0)
        
        summary.columns = [
            'job_count',
            'min_of_min_salaries',
            'avg_of_min_salaries',
            'max_of_min_salaries',
            'min_of_max_salaries',
            'avg_of_max_salaries',
            'max_of_max_salaries',
            'average_salary',
            'average_salary_range'
        ]
        
        return summary.reset_index()
    
    def save_to_csv(self, df: pd.DataFrame, output_path: str) -> str:
        """Save DataFrame to CSV file"""
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return output_path
    
    def get_csv_data(self, df: pd.DataFrame) -> str:
        """Return DataFrame as CSV string"""
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    def convert_and_save(self, output_dir: str = "results") -> dict:
        """
        Main conversion method: load JSON, convert to DataFrame, and save as CSV
        Returns dictionary with file paths and CSV data
        """
        # Load and convert data
        json_data = self.load_json_data()
        df_all_jobs = self.convert_to_dataframe(json_data)
        df_summary = self.get_category_summary(df_all_jobs)
        
        # Prepare output paths
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(exist_ok=True)
        
        all_jobs_path = output_dir_path / "paylab_all_jobs.csv"
        summary_path = output_dir_path / "paylab_category_summary.csv"
        
        # Save to files
        self.save_to_csv(df_all_jobs, str(all_jobs_path))
        self.save_to_csv(df_summary, str(summary_path))
        
        # Get CSV data as strings
        all_jobs_csv = self.get_csv_data(df_all_jobs)
        summary_csv = self.get_csv_data(df_summary)
        
        # Generate statistics
        stats = {
            'total_categories': df_all_jobs['category'].nunique(),
            'total_jobs': len(df_all_jobs),
            'overall_min_salary': float(df_all_jobs['job_min_salary'].min()),
            'overall_max_salary': float(df_all_jobs['job_max_salary'].max()),
            'overall_avg_salary': float(df_all_jobs['job_average_salary'].mean()),
            'median_avg_salary': float(df_all_jobs['job_average_salary'].median())
        }
        
        return {
            'files': {
                'all_jobs': str(all_jobs_path),
                'category_summary': str(summary_path)
            },
            'csv_data': {
                'all_jobs': all_jobs_csv,
                'category_summary': summary_csv
            },
            'statistics': stats
        }


def main():
    """Main function to run the converter"""
    converter = PaylabDataConverter()
    result = converter.convert_and_save()
    
    return result


if __name__ == "__main__":
    main()
