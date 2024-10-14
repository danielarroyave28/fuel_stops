

def optimize_route(self):
       
       print(self.current_location)
       
       nodes_cumulative_dist = self.calculate_cumulative_distances()
       
       if self.total_distance <= 500:

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
          
       elif self.total_distance > 500:
          
          
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
          self.remaining_distance -= self.cumulative_distance
          print(f"remain distance at top: {self.remaining_distance}")
          self.route_coords = [i for i in self.route_coords if i["node"] >= node]
          
          if self.remaining_distance <= 500:

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
                  
              
          while self.remaining_distance > 500:
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
              self.remaining_distance -= self.cumulative_distance
              print(f"remain distance at bot: {self.remaining_distance}")
              self.route_coords = [i for i in self.route_coords if i["node"] >= node]
              
              print(self.route_coords)
              
              #last leg to add
              if self.remaining_distance < 500:
                  last_distance = self.remaining_distance
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
              