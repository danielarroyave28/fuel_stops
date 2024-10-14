import pandas as pd
from typing import List, Dict
from geopy.distance import geodesic

class FuelRouteOptimizer:
    
    def __init__(self, truck_stops: pd.DataFrame, route_coords: List[Dict], 
                 autonomy: int, mpg: int, start_city: str, finish_city: str):
        
        self.truck_stops = truck_stops
        self.route_coords = route_coords
        self.autonomy = autonomy
        self.mpg = mpg
        self.fuel_stops = []
        self.total_distance = sum(step['distance'] for step in self.route_coords)
        self.remaining_distance = self.total_distance # starting point
        self.cumulative_distance = 0.0
        self.current_location = route_coords[0]
        self.start_city = start_city
        self.finish_city = finish_city
        self.cities = [start_city, finish_city]
        self.max_gallons = 50
        
        self.cumulative_distances = []
        
        
    def calculate_cumulative_distances(self):
      """Calculate cumulative distances for each node in the route."""
      cumulative_distance = 0.0
      self.cumulative_distances = []  # Reset the list to ensure it starts fresh
      
      for step in self.route_coords:
          cumulative_distance += step['distance']
          self.cumulative_distances.append({
              'node': step['node'],  
              'cumulative_distance': cumulative_distance
          })
      
      return self.cumulative_distances
      
    
    def filter_stops(self, max_distance=10, buffer_distance=2.0) -> pd.DataFrame:
      """
      Check which stops are within max_distance radius search. Then filters out fuel stops
      according to more conditions (not start_city, finish_city) and cheapest fuel price
      """
      
      self.filter_stops_by_bounding_box(buffer_distance)
      
      def min_distance_to_route(stop_row):
        stop_location = (stop_row['lat_city'], stop_row['lon_city'])
        min_distance = float('inf')  # Initialize to infinity
        nearest_point = None

        # Check the distance from the stop to each route point
        for point in self.route_coords:
            point_coords = (point['latitude'], point['longitude'])
            distance = geodesic(point_coords, stop_location).miles
            
            # Update the minimum distance and nearest point if applicable
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
                
        return pd.Series([min_distance, nearest_point])


      # Calculate the minimum distance from each stop to the route
      self.truck_stops[['min_distance', 'nearest_route_point']] = self.truck_stops.apply(min_distance_to_route, axis=1)

      # Exclude stops in the start and finish cities
      reachable_stops = self.truck_stops[
          (self.truck_stops['min_distance'] <= max_distance) & 
          (~self.truck_stops['City'].isin(self.cities))
      ]
      
      print(f"reachable_stops: {reachable_stops}")
      
      if not reachable_stops.empty:
        cheapest_stop = reachable_stops.loc[reachable_stops['Retail Price'].idxmin()]
      else:
        print("No reachable stops found.")

      return cheapest_stop

    def calculate_fuel_needs_and_cost(self, distance: float, fuel_price: float) -> float:
        """Calculate the fuel cost for a given distance."""
        gallons_needed = distance / self.mpg
        total_cost = gallons_needed * fuel_price
        return gallons_needed, total_cost
      
    def calculate_bounding_box(self, buffer_distance=2.0):
      """
      Calculate a bounding box around the route with a given buffer distance (in degrees).
      buffer_distance: the distance to extend the box beyond the route coordinates.
      This is done to pre filter the dataframe of fuel stops, like this the fuel stop search
      filtering will be faster.
      """
      latitudes = [step['latitude'] for step in self.route_coords]
      longitudes = [step['longitude'] for step in self.route_coords]

      min_lat, max_lat = min(latitudes) - buffer_distance, max(latitudes) + buffer_distance
      min_lon, max_lon = min(longitudes) - buffer_distance, max(longitudes) + buffer_distance

      return min_lat, max_lat, min_lon, max_lon

    def filter_stops_by_bounding_box(self, buffer_distance=2.0):
        """
        Filter stops that fall within the bounding box around the route.
        buffer_distance: the distance to extend the box beyond the route coordinates.
        """
        min_lat, max_lat, min_lon, max_lon = self.calculate_bounding_box(buffer_distance)

        # Filter the stops within the bounding box
        self.truck_stops = self.truck_stops[
            (self.truck_stops['lat_city'] >= min_lat) &
            (self.truck_stops['lat_city'] <= max_lat) &
            (self.truck_stops['lon_city'] >= min_lon) &
            (self.truck_stops['lon_city'] <= max_lon)
        ]
        
        
    def optimize_route(self):
       
       print(self.current_location)
       
       nodes_cumulative_dist = self.calculate_cumulative_distances()
       
       if self.total_distance <= self.autonomy:

          #filter the cheapest stop at start city and fuel up the necessary 
          
          dff = self.truck_stops.loc[self.truck_stops["City"] == self.start_city]
          
          dff = dff.loc[dff["Retail Price"].idxmin()]
          fuel_price = dff["Retail Price"]
          print(dff["Retail Price"])
          
          gallons_needed, total_cost = self.calculate_fuel_needs_and_cost(self.total_distance, fuel_price)
    
          print(f"Gallons Needed: {gallons_needed:.2f}")
          print(f"Total Cost: ${total_cost:.2f}")
          
          return {
            "Stop Name": dff["Truckstop Name"],
            "Refuel City": dff["City"],
            "Stop Location_longitude": dff["lon_city"],
            "Stop Location Latitude": dff["lat_city"],
            "Gallons Needed": round(gallons_needed, 2),
            "fuel_cost": round(total_cost, 2),  
          }
          
       elif self.total_distance > self.autonomy:
          
          
          all_stops = []
          #First calculate the nearest/cheapest stop
          cheapest_stop = self.filter_stops()
          print("----------------------")
          print(cheapest_stop)
          
          #check the distance reached until node of next stop

          node = cheapest_stop["nearest_route_point"]["node"]
          node_prev = cheapest_stop["nearest_route_point"]["node"] - 1
          fuel_price = cheapest_stop["Retail Price"]
          
          node_info_prev = next((item for item in nodes_cumulative_dist if item['node'] == node_prev), None)
          
          print(node_info_prev)
          
          travelled_distance_prev = node_info_prev["cumulative_distance"]
          
          dff = self.truck_stops.loc[self.truck_stops["City"] == self.start_city]
          
          dff = dff.loc[dff["Retail Price"].idxmin()]
          fuel_price = dff["Retail Price"]
          
          gallons_needed, total_cost = self.calculate_fuel_needs_and_cost(travelled_distance_prev, fuel_price)
          
          print(f"Gallons Needed: {gallons_needed:.2f}")
          print(f"Total Cost: ${total_cost:.2f}")
          
          all_stops.append({
            "Stop Name": dff["Truckstop Name"],
            "Refuel City": dff["City"],
            "Stop Location_longitude": dff["lon_city"],
            "Stop Location Latitude": dff["lat_city"],
            "Gallons Needed": round(gallons_needed, 2),
            "fuel_cost": round(total_cost, 2),
            "fuel_price": fuel_price
          })
          
          self.cumulative_distance += travelled_distance_prev    
          print(self.cumulative_distance)
          self.remaining_distance -= self.cumulative_distance
          print(f"remain distance at top: {self.remaining_distance}")
          self.route_coords = [i for i in self.route_coords if i["node"] >= node]
          
          if self.remaining_distance <= self.autonomy:

              #calculate the refueling cost at detected cheapest stop
              gallons_needed, total_cost = self.calculate_fuel_needs_and_cost(self.remaining_distance, cheapest_stop["Retail Price"])
              
              all_stops.append({
                "Stop Name": cheapest_stop["Truckstop Name"],
                "Refuel City": cheapest_stop["City"],
                "Stop Location_longitude": cheapest_stop["lon_city"],
                "Stop Location Latitude": cheapest_stop["lat_city"],
                "Gallons Needed": round(gallons_needed, 2),
                "fuel_cost": round(total_cost, 2),
                "fuel_price": cheapest_stop["Retail Price"] 
              })
              
              return all_stops
                  
              
          while self.remaining_distance > self.autonomy:
              #calculate same process
              #update start point first
              
              next_cheapest_stop = self.filter_stops()
              node_prev = next_cheapest_stop["nearest_route_point"]["node"] - 1
              node = next_cheapest_stop["nearest_route_point"]["node"]
              
              node_info_prev = next((item for item in nodes_cumulative_dist if item['node'] == node_prev), None)
              travelled_distance_prev = node_info_prev["cumulative_distance"]

              gallons_needed, total_cost = self.calculate_fuel_needs_and_cost(travelled_distance_prev, cheapest_stop["Retail Price"])
              
              print(f"Gallons Needed: {gallons_needed:.2f}")
              print(f"Total Cost: ${total_cost:.2f}")
              
              all_stops.append({
                "Stop Name": cheapest_stop["Truckstop Name"],
                "Refuel City": cheapest_stop["City"],
                "Stop Location_longitude": cheapest_stop["lon_city"],
                "Stop Location Latitude": cheapest_stop["lat_city"],
                "Gallons Needed": round(gallons_needed, 2),
                "fuel_cost": round(total_cost, 2),
                "fuel_price": cheapest_stop["Retail Price"]
              })
              
              self.cumulative_distance += travelled_distance_prev
              print(self.cumulative_distance)    
              self.remaining_distance -= self.cumulative_distance
              print(f"remain distance at bot: {self.remaining_distance}")
              self.route_coords = [i for i in self.route_coords if i["node"] >= node]
              
              print(self.route_coords)
              
              #last leg to add
              if self.remaining_distance < self.autonomy:
                  last_distance = self.total_distance - self.cumulative_distance
                  gallons_needed_last, total_cost_last = self.calculate_fuel_needs_and_cost(last_distance, next_cheapest_stop["Retail Price"])
                  all_stops.append({
                    "Stop Name": next_cheapest_stop["Truckstop Name"],
                    "Refuel City": next_cheapest_stop["City"],
                    "Stop Location_longitude": next_cheapest_stop["lon_city"],
                    "Stop Location Latitude": next_cheapest_stop["lat_city"],
                    "Gallons Needed": round(gallons_needed_last, 2),
                    "fuel_cost": round(total_cost_last, 2),
                    "fuel_price": next_cheapest_stop["Retail Price"]
                  })
                  
              
          return all_stops
              
              

              
              
             
            
              
              
          
          
          
        
          
          
          
 