# data_extraction_simulator.py

import pandas as pd
import numpy as np
import datetime
import random
import uuid

# --- Project Constants ---
PROJECT_NAME = "SPL-AgriSense"
MOCK_FERTILIZER_SHOP_CONTACT = "9988776655" # Indian mobile number format

# --- Utility Functions ---

def generate_random_soil_data():
    """Generates a realistic set of random soil composition and nutrient data."""
    data = {
        # Soil Constituents (Percentages)
        'Organic_Matter_pct': round(random.uniform(0.5, 5.0), 2),
        'Clay_pct': round(random.uniform(10, 40), 2),
        'Silt_pct': round(random.uniform(20, 50), 2),
        'Sand_pct': round(100 - (random.uniform(0.5, 5.0) + random.uniform(10, 40) + random.uniform(20, 50)), 2), # Ensuring sum is 100 (approx)
        
        # Nutrients (PPM)
        'Nitrogen_ppm': random.randint(50, 400),
        'Phosphorus_ppm': random.randint(10, 80),
        'Potassium_ppm': random.randint(100, 500),
        'pH_value': round(random.uniform(5.5, 8.5), 1),
        'EC_mS_cm': round(random.uniform(0.1, 4.0), 2), # Electrical Conductivity
    }
    # Adjust Sand to make it sum to 100 for simplicity in simulation
    data['Sand_pct'] = max(0, 100 - data['Organic_Matter_pct'] - data['Clay_pct'] - data['Silt_pct'])
    return data

def generate_simulation_output(user_contact_or_email, name, location_name):
    """
    Simulates the data output from the SPL-AgriSense device.
    In a real scenario, this would be an API call or a file dump.
    """
    
    # Simulate Geo-location for a few Indian cities
    location_map = {
        "Pune, India": (18.5204, 73.8567),
        "Patna, India": (25.5941, 85.1376),
        "Ludhiana, India": (30.9010, 75.8573),
        "Hyderabad, India": (17.3850, 78.4867),
        "Kanpur, India": (26.4499, 80.3319),
    }
    
    # Use location_name to pick a geo-coordinate, or a random one if not mapped
    geo_loc = location_map.get(location_name, (random.uniform(10, 35), random.uniform(70, 88)))

    # Simulate YOLO model output (Current Crop)
    crops = ["Paddy", "Wheat", "Maize", "Sugarcane", "None Detected"]
    # 70% chance of a crop being present
    crop_present = random.choices(crops, weights=[0.2, 0.2, 0.2, 0.1, 0.3], k=1)[0]
    
    # Assemble the final data record
    data_record = {
        'Test_ID': str(uuid.uuid4()), # Unique ID for this test
        'Device_User_Name': name,
        'User_Contact_or_Email': user_contact_or_email,
        'Test_Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Location_Name': location_name,
        'Latitude': round(geo_loc[0], 4),
        'Longitude': round(geo_loc[1], 4),
        'Crop_Detected': crop_present,
        'Crop_Health_Index': round(random.uniform(0.5, 1.0) if crop_present != "None Detected" else 0.0, 2), # Simulated health index
        **generate_random_soil_data() # Unpack all soil data
    }
    
    return data_record

# --- Main Simulation Function ---
def simulate_new_soil_test(user_credential, user_name, field_location):
    """
    Simulates a new soil test and returns the data record.
    In a real system, this function would receive input from the physical device.
    """
    print(f"\n[SIMULATION] Device testing soil for: {user_name} ({user_credential}) at {field_location}...")
    
    # In a real system, you would check the database here if the user is registered.
    # For this file, we just generate the data.
    
    test_data = generate_simulation_output(user_credential, user_name, field_location)
    
    print(f"[SIMULATION] Data recorded (ID: {test_data['Test_ID']}).")
    return test_data

# --- Example Usage (Not needed in the final app, just for testing) ---
if __name__ == '__main__':
    # Simulating a successful test for a known user
    test_data_success = simulate_new_soil_test(
        user_credential="user@example.com", 
        user_name="Shashank Kumar", 
        field_location="Pune, India"
    )
    print("\n--- Simulated Test Result (Success) ---")
    print(pd.Series(test_data_success).to_string())

    # Simulating a test for a user NOT yet signed up
    test_data_new_user = simulate_new_soil_test(
        user_credential="newfarmer@mail.com",
        user_name="Gopal Varma",
        field_location="Kanpur, India"
    )
    print("\n--- Simulated Test Result (New User) ---")
    print(pd.Series(test_data_new_user).to_string())
    
    # This data would then be pushed to your main app's database/session state.
