
import requests
import json


URL="https://data.1212.mn:443/api/v1/mn/NSO/Labour, business/Wages/MONTHLY AVERAGE NOMINAL WAGES, by occupation and gender/DT_NSO_0400_025V1.px"
QUERY={
  "query": [
    {
      "code": "Хүйс",
      "selection": {
        "filter": "item",
        "values": [
          "0",
          "1",
          "2"
        ]
      }
    },
    {
      "code": "Ажил мэргэжлийн ангилал",
      "selection": {
        "filter": "item",
        "values": [
          "0",
          "1",
          "2",
          "3",
          "4",
          "5",
          "6",
          "7",
          "8",
          "9",
          "10"
        ]
      }
    },
    {
      "code": "Он",
      "selection": {
        "filter": "item",
        "values": [
          "0"
        ]
      }
    }
  ],
  "response": {
    "format": "json-stat2"
  }
}

def fetch_salary_statistics():
    try:
        response = requests.post(URL, json=QUERY)
        response.raise_for_status()
        data = response.json()


        #fix data into  table format
        gender_labels = data['dimension']['Хүйс']['category']['label']
        #Ажил мэргэжлийн ангилал
        category_labels = data['dimension']['Ажил мэргэжлийн ангилал']['category']['label']
        #Он
        year_labels = data['dimension']['Он']['category']['label']
        #Extract values
        values = data['value']
        # Create structured DataFrame
        rows = []
        idx = 0
        for gender_key, gender_value in gender_labels.items():
            for category_key, category_value in category_labels.items():
                for year_key, year_value in year_labels.items():
                    rows.append({
                        'Gender': gender_value,
                        'Category': category_value.replace('\n', ' ').strip(),
                        'Year': year_value,
                        'value': values[idx]
                    })
                    idx += 1
    
        
        # Save the fetched data to a JSON file
        with open("data/salary_statistics.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=4)
        
        print("Salary statistics data fetched and saved to data/salary_statistics.json")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching salary statistics: {e}")
        return None
if __name__ == "__main__":
    fetch_salary_statistics()