from app.services.rappi_kfc_scraper import RappiKFCScraper
from app.services.geo_handler import GeoHandler


rappi_scraper = RappiKFCScraper()


user_locations = GeoHandler.get_random_locations(quantity=1)

rappi_scraper.run(user_locations)



    
    





