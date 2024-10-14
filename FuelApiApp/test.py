import pandas as pd

df = pd.read_csv('cleaned_fuel_data.csv')

print(df.info())

print(df['lat_truck'].isna().sum())
print(df['lon_truck'].isna().sum())

df2 = df[df['City'] == 'Denver']
print(df2)