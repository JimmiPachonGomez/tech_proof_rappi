from app.services.rappi_kfc_scraper import RappiKFCScraper
from app.services.geo_handler import GeoHandler
from app.services.uber_eats_kfc_scraper import UberEatsKFCScraper
from concurrent.futures import ThreadPoolExecutor


user_locations = GeoHandler.get_random_locations(quantity=1)



rappi_scraper = RappiKFCScraper()



uber_eats_scraper = UberEatsKFCScraper()

uber_eats_scraper.run(user_locations)
rappi_scraper.run(user_locations)


# with ThreadPoolExecutor(max_workers=3) as executor:
#     executor.submit(uber_eats_scraper.run,user_locations)
#     executor.submit(rappi_scraper.run,user_locations)
    