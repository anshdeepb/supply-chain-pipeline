import requests

API_URL = "https://bx95pjlrwe.execute-api.us-east-1.amazonaws.com/prod/predict"

payload = {
  "num_refill_req_l3m": 8,
  "workers_num": 55,
  "retail_shop_num": 6200,
  "dist_from_hub": 80,
  "zone": "South",
  "WH_capacity_size": "Small",
  "Location_type": "Rural",
  "wh_owner_type": "Company",
  "approved_wh_govt_certificate": "A+",
  "WH_regional_zone": "Zone 4",
  "transport_issue_l1y": 3,
  "Competitor_in_mkt": 5,
  "distributor_num": 60,
  "flood_impacted": 1,
  "flood_proof": 0,
  "electric_supply": 1,
  "wh_est_year": 2005,
  "storage_issue_reported_l3m": 5,
  "temp_reg_mach": 0,
  "wh_breakdown_l3m": 2,
  "govt_check_l3m": 6
}

response = requests.post(API_URL, json=payload)
print(response.json())