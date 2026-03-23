import json
import random
import re


class GeoHandler:


    @staticmethod
    def get_random_locations(quantity,file_path="locations.json"):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        locations = random.choices(data, k=quantity)
            
        return locations
    
    @staticmethod
    def extract_postal_code(address:str)->int:
        coincidences = re.findall(r'\b\d{5}\b', address)
        
        return coincidences[-1] if coincidences else None
    
