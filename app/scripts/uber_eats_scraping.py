from app.services.uber_eats_kfc_scraper import UberEatsKFCScraper
from app.services.geo_handler import GeoHandler


uber_eats_scraper = UberEatsKFCScraper()


user_locations = GeoHandler.get_random_locations(quantity=1)

uber_eats_scraper.run(user_locations)



    
    

