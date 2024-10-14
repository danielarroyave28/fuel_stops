import pandas as pd
import requests
from urllib.parse import quote
import time
from dotenv import load_dotenv

import os
load_dotenv()




api_key = os.getenv("api_key")

def clean_dataframe(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename)
    print(len(df))
    
    # Group the dataframe and select the first value for each grouped ID, while averaging the 'Retail Price'
    df2 = df.groupby(['OPIS Truckstop ID', 'Address']).agg({
        'Truckstop Name': 'first',
        #'Address': 'first',
        'City': 'first',
        'State': 'first',
        'Rack ID': 'first',
        'Retail Price': 'mean'
    }).reset_index()
    
    # For loop to create lat/long for each truckstop
    latitudes = []
    longitudes = []
    latitudes_cities = []
    longitudes_cities = []
    #df2 = df2[0:50]
    
    for i, row in df2.iterrows():
        address = f"{row['Truckstop Name']}"
        if '#' in address:
            address_fix = address.split('#')[0].strip()
            final_address = f"{address_fix}, +{row['City']}, +{row['State']}"
        else:
            final_address = f"{row['Truckstop Name']}, +{row['City']}, +{row['State']}"
        
        location = get_location(final_address, api_key)
        city_query = f"{row['City']}, +{row['State']}"
        location_city = get_location(city_query, api_key)
        print(f"location at top: {location}")
        
        if location.get('lat') == '' or location.get('lng') == '':
            # Retry with address and not truckstop name
            address_name = f"{row['Address']}"
            if "&" in address_name:
                address_fix_2 = address_name.split('&')[0].strip()
                final_address_2 = f"{address_fix_2}, +{row['City']}, +{row['State']}"
            else:
                final_address_2 = f"{row['Address']}, +{row['City']}, +{row['State']}"
            
            print(f"final_address_2: {final_address_2}")
            location = get_location(final_address_2, api_key)
            print(f"location at bottom: {location}")
        
        latitudes.append(location.get('lat'))
        longitudes.append(location.get('lng'))
        latitudes_cities.append(location_city.get('lat'))
        longitudes_cities.append(location_city.get('lng'))
    
    df2["lat_truck"] = latitudes
    df2["lon_truck"] = longitudes
    df2["lat_city"] = latitudes_cities
    df2["lon_city"] = longitudes_cities
    
    
    df2.to_csv('cleaned_fuel_data.csv')
    
    return df2

def get_location(address: str, api_key: str) -> dict:
    encoded_address = quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
    
    try: 
        response = requests.get(url).json()
        location = response['results'][0]['geometry']['location']
    except Exception as e:
        print(f"Error for address: {address} - {e}")
        print(f"Skipping address: {encoded_address}")
        location = {
            'lat': '',
            'lng': ''
        }
    
    return location

def create_cities_df(filename: str):
    
    df = pd.read_csv(filename)
    
    df['City'] = df['City'].str.strip()
    df['State'] = df['State'].str.strip()
    
    df2 = df[['City', 'State', 'lat_city', 'lon_city']].drop_duplicates()
    
    return df2

if __name__ == "__main__":
    
    
    # Load and clean the data
    # df = clean_dataframe('fuel-prices-for-be-assessment.csv')

    # # Display the updated DataFrame
    # print(df.head(100))
    # print(len(df))
    # print(df.loc[df['OPIS Truckstop ID'] == 105])

    # # Example response for a specific address
    # response = get_location('TA SAGINAW I 75 TRAVEL CENTER, +Bridgeport, +MI', api_key)
    # print(response)

    df = create_cities_df("cleaned_fuel_data.csv")
    
    df.to_csv("city_states_with_loc.csv", index=False)
    
    print(df.head(100))
    
    city_state_counts = df.groupby('City')['State'].nunique()
    cities_with_multiple_states = city_state_counts[city_state_counts > 1]
    print("Cities with the same name in different states:")
    print(cities_with_multiple_states)
    
    print(df[df["City"] == "Great Falls"])