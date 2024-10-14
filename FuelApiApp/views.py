from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .algo import FuelRouteOptimizer
from .serializers import RouteInputSerializer
import pandas as pd
import requests
from dotenv import load_dotenv
import os

load_dotenv()


key = os.getenv("key")

# Create your views here.
@api_view(['GET', 'POST'])
def fuel(request):
  return Response('List of fuel prices', 
                  status=status.HTTP_200_OK)
  
class FuelList(APIView):
    def get(self, request):
        return Response('List of fuel prices', 
                  status=status.HTTP_200_OK)
        
    def post(self, request):
        serializer = RouteInputSerializer(data=request.data)
        if serializer.is_valid():
            start_city = serializer.validated_data["start_city"]
            start_state = serializer.validated_data["start_state"]
            finish_city = serializer.validated_data["finish_city"]
            finish_state = serializer.validated_data["finish_state"]
            
            #filter dataframe to get coordinates for starting point and end point
            df = pd.read_csv('city_states_with_loc.csv')
            
             # Filter the DataFrame for the starting location
            start_filter = df[(df["City"].str.upper() == start_city.upper()) & 
                            (df["State"].str.upper() == start_state.upper())]
            

            # Filter the DataFrame for the finishing location
            finish_filter = df[(df["City"].str.upper() == finish_city.upper()) & 
                            (df["State"].str.upper() == finish_state.upper())]
            
            
            start_lat = start_filter.iloc[0]['lat_city']
            start_lon = start_filter.iloc[0]['lon_city']
            finish_lat = finish_filter.iloc[0]['lat_city']
            finish_lon = finish_filter.iloc[0]['lon_city']
                    
            if start_filter.empty:
                return Response({"error": "Starting location not found."}, status=status.HTTP_400_BAD_REQUEST)

            if finish_filter.empty:
                return Response({"error": "Finishing location not found."}, status=status.HTTP_400_BAD_REQUEST)
                    
            #perform request to mapbox
            mapbox_url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start_lon},{start_lat};{finish_lon},{finish_lat}?access_token={key}&steps=true"
            response = requests.get(mapbox_url)
            if response.status_code == 200:
                data = response.json()
                #grab all the coordinates in the steps woth the respective distance travelled
                steps = data["routes"][0]["legs"][0]["steps"]
                
                my_list = []
                for i, step in enumerate(steps, start=1):
                    dist = float(step["distance"]) * 0.000621371
                    lon = step["maneuver"]["location"][0]
                    lat  = step["maneuver"]["location"][1]
                    my_list.append({
                        'node': i,
                        'longitude': lon,
                        'latitude': lat,
                        'distance': dist
                    })
                    
                total_distance = sum(step['distance'] for step in my_list)   
                
                stops = pd.read_csv('FuelApiApp/cleaned_fuel_data.csv')
                stops["City"] = stops["City"].str.strip()
                
                fuel_calc = FuelRouteOptimizer(truck_stops=stops, route_coords=my_list, autonomy=500, mpg=10,
                                               start_city=start_city, finish_city=finish_city)
                
                stops = fuel_calc.optimize_route()

                total_cost = sum(i['fuel_cost'] for i in stops)
                
                return Response({
                    'start_location': start_city.lower(),
                    'start_lat': start_lat,
                    'start_lon': start_lon,
                    'finish_location': finish_city.lower(),
                    'finish_lat': finish_lat,
                    'finish_lon': finish_lon,
                    'steps': my_list,
                    'stops_info': stops,
                    'total_distance': round(total_distance,2),
                    'total_cost': round(total_cost,2)
                    
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to fetch directions."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)