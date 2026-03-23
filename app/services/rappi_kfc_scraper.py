from app.utils.request_handler import RequestHandler
from bs4 import BeautifulSoup
import json
from .geo_handler import GeoHandler
from app.utils.logger import logger
from datetime import datetime,timezone
from app.models import DeliveryRegister, Payload, Product, Store
from app.utils.config import RAPPI_TOKEN
from .data_loader import DataLoader



class RappiKFCScraper:

    def __init__(self):

        self.base_url = "https://www.rappi.com.mx"
        self.token = RAPPI_TOKEN
        self.brand_id = 2096 #brand_id=2096 es KFC en la plataforma de Rappi
        self.city = "Ciudad de Mexico"
        self.data_loader = DataLoader()


    def run(self, user_locations):
        payloads = self._build_payloads(user_locations)

        payloads_dict = [payload.model_dump(mode="json") for payload in payloads]

        with open("rappi.json", 'w', encoding='utf-8') as f:
            json.dump(payloads_dict, f, indent=4, ensure_ascii=False)

        self.data_loader.upload_data(payloads_dict)

        logger.info("Scraping de Uber Eats finalizado")


    def _build_payloads(self,user_locations) -> list[Payload]:

        stores_cm = self._get_stores()

        all_data = []

        for store in stores_cm:
            
            for user_location in user_locations:
                logger.info(f"STORE_ID: {store["store_id"]}  LOCATION: {user_location}")
                delivery_data = self._get_delivery_data(store["store_id"],user_location)

                if not delivery_data:
                    continue
                    
                store["latitude"] = delivery_data["location"][1]
                store["longitude"] = delivery_data["location"][0] 

                store_obj = Store.model_validate(store)

            
                for corridor in delivery_data["corridors"]:
                    for product_info in corridor["products"]:
                        
                        product = self._build_product(product_info)
                        delivery_register = self._build_delivery_register(delivery_data,product_info,user_location)

                        payload = Payload(store=store_obj,
                                          product=product,
                                          delivery_register=delivery_register)

                        all_data.append(payload)
        
        return all_data


    def _build_delivery_register(self,delivery_data:dict,product_info:dict,user_location:dict)->DeliveryRegister:
        delivery_register = {}
        delivery_register["store_id"] = delivery_data["store_id"] 
        delivery_register["open_time"] = delivery_data["schedules"][0]["open_time"]
        delivery_register["close_time"] = delivery_data["schedules"][0]["close_time"]
        delivery_register["eta"] = int(delivery_data["eta"].replace("min","").strip())
        delivery_register["percentage_service_fee"] = delivery_data["percentage_service_fee"]
        delivery_register["product_id"] = product_info["product_id"]
        delivery_register["store_status"] = delivery_data["status"]
        delivery_register["price"] = product_info["real_price"]
        delivery_register["discount_percentage"] = product_info["discount_percentage"]
        delivery_register["ui_price"] = round(delivery_register["price"]*(1 - abs(delivery_register["discount_percentage"])/100))
        delivery_register["eta_cost"] = delivery_data["eta_value"] or 0.0
        delivery_register["real_price"] = round(delivery_register["ui_price"]*(1 + abs(delivery_data["percentage_service_fee"])/100)) + delivery_register["eta_cost"]
        delivery_register["created_at"] = datetime.now(timezone.utc).isoformat() 
        delivery_register["user_latitude"] = user_location["lat"]
        delivery_register["user_longitude"] = user_location["lng"]
        delivery_register["company"] = "Rappi"

        return DeliveryRegister.model_validate(delivery_register)
    

    def _build_product(self,product_info:dict):
        product = {}
        product["product_id"] = product_info["product_id"]
        product["name"] = product_info["name"]
        product["description"] = product_info["description"]
        product["store_id"] = product_info["store_id"]
        
        return Product.model_validate(product)
    

    def _get_stores(self):

        brand_url = f"{self.base_url}/ciudad-de-mexico/restaurantes/delivery/{self.brand_id}"

        store_url = self.base_url + "{friendly_href}"

        response = RequestHandler.do_request(method="GET",url=brand_url)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        

        script = soup.find('script',id="__NEXT_DATA__").text

        next_data_json = json.loads(script)

        stores = next_data_json["props"]["pageProps"]["brand"]["stores"]

        stores_cm =  [{"store_id":store["storeId"],
                        "name":store["name"],
                        "url":store_url.format(friendly_href=store["friendlyUrl"]),
                        "address":store["address"],
                        "postal_code":GeoHandler.extract_postal_code(store["address"])
                        } 

                        for store in stores

                        if self.city.casefold() in store["address"].casefold().replace("é","e")
                        ]
        return stores_cm
    

    def _get_delivery_data(self,store_id,delivery_location):

        url = f"https://services.mxgrability.rappi.com/api/web-gateway/web/restaurants-bus/store/id/{store_id}"

        payload = {
            "lat": delivery_location["lat"],
            "lng": delivery_location["lng"],
            "store_type": "restaurant",
            "is_prime": False,
            "prime_config": {"unlimited_shipping": False}
        }
        headers = {
            "accept": "application/json",
            "accept-language": "es-MX",
            "access-control-allow-headers": "*",
            "access-control-allow-origin": "*",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json; charset=UTF-8",
            "origin": "https://www.rappi.com.mx",
            "priority": "u=1, i",
            "referer": "https://www.rappi.com.mx/",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        }
        
        response = RequestHandler.do_request(method="POST",url=url, body=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            error_json = response.json()
            if error_json["error"]["code"] == "bus.invalid_microzone":
                return
        else:
            raise Exception(f"Hubo un error obteniendo delivery_data | status code:{response.status_code} | respuesta: {response.text}")





    