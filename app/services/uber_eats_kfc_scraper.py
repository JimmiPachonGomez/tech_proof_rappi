from app.utils.request_handler import RequestHandler
import json
from app.utils.logger import logger
from datetime import datetime,timezone
from app.models import DeliveryRegister, Payload, Product, Store
from app.utils.config import RAPPI_TOKEN
import re
from .data_loader import DataLoader


class UberEatsKFCScraper:

    def __init__(self):

        self.base_url = "https://www.ubereats.com"
        self.city = "Mexico city" 
        self.data_loader = DataLoader()


    def run(self, user_locations):
        payloads = self._build_payloads(user_locations)

        payloads_dict = [payload.model_dump(mode="json") for payload in payloads]

        with open("uber_eats.json", 'w', encoding='utf-8') as f:
            json.dump(payloads_dict, f, indent=4, ensure_ascii=False)

        self.data_loader.upload_data(payloads_dict)

        logger.info("Scraping de Uber Eats finalizado")


    def _build_payloads(self,user_locations) -> list[Payload]:

        all_data = []

        kfc_store_ids = self._get_store_ids()


        for kfc_store_id in kfc_store_ids:
            
            for user_location in user_locations:
                delivery_data = self._get_delivery_data(kfc_store_id, user_location)

                store = self._build_store(delivery_data)

                items = []
                for key,value in delivery_data["catalogSectionsMap"].items():
                    for element in value:
                        items += element["payload"]["standardItemsPayload"]["catalogItems"] if element.get("payload").get("standardItemsPayload") else []

                
                for item in items:
                    
                    product = self._build_product(item,delivery_data)

                    delivery_register = self._build_delivery_register(delivery_data,item,user_location)

                    payload = Payload(store=store,
                                      product=product,
                                      delivery_register=delivery_register)
                    
                    all_data.append(payload)
            
        return all_data
    

    def _build_delivery_register(self,delivery_data:dict,item:dict,user_location:dict)->DeliveryRegister:
        delivery_register = {}
        delivery_register["store_id"] = delivery_data["uuid"]
        delivery_register["open_time"] = self._from_minutes_to_time(delivery_data["hours"][0]["sectionHours"][0]["startTime"])
        delivery_register["close_time"] = self._from_minutes_to_time(delivery_data["hours"][0]["sectionHours"][0]["endTime"])
        delivery_register["eta"] = int(delivery_data["etaRange"]["text"].split("-")[0].strip())
        delivery_register["eta_cost"] = self._extract_eta_cost(delivery_data["fareBadge"]["text"])
        delivery_register["user_latitude"] = user_location["lat"]
        delivery_register["user_longitude"] = user_location["lng"]
        delivery_register["created_at"] = datetime.now(timezone.utc).isoformat() 
        delivery_register["store_status"] = delivery_data["storeInfoMetadata"]["storeAvailablityStatus"]["state"]
        delivery_register["service_fee"] = delivery_data["fareInfo"]["serviceFee"]
        delivery_register["ui_price"] = item["price"]/100

        delivery_register["price"] = (float(item["priceTagline"]["accessibilityText"].split(",")[1].replace(" discounted from $","")) 
                                        if "discounted from" in item["priceTagline"]["accessibilityText"] else delivery_register["ui_price"])
        
        delivery_register["real_price"] = delivery_register["ui_price"]+delivery_register["eta_cost"]+delivery_register["service_fee"]
        delivery_register["product_id"] = item["uuid"]
        
        delivery_register["discount_percentage"] = (delivery_register["price"]-delivery_register["ui_price"])*100/delivery_register["price"]
        delivery_register["company"] = "Uber Eats"

        return DeliveryRegister.model_validate(delivery_register)
    

    def _build_product(self,item:dict,delivery_data):
        product = {}
        product["product_id"] = item["uuid"]
        product["name"] = item["title"]
        product["description"] = item["itemDescription"]
        product["store_id"] = delivery_data["uuid"]
        
        return Product.model_validate(product)
    

    def _build_store(self,delivery_data:dict):
        store = {}
        store["store_id"] = delivery_data["uuid"]
        store["name"] = delivery_data["title"]
        store["url"] = None
        store["address"] =  delivery_data["location"]["address"]
        store["postal_code"] = delivery_data["location"]["postalCode"]
        store["latitude"] = delivery_data["location"]["latitude"]
        store["longitude"] = delivery_data["location"]["longitude"]

        return Store.model_validate(store)
    

    def _get_stores_by_page(self,page):
        url = f"{self.base_url}/_p/api/getPaginatedStoresV1"

        querystring = {"localeCode":"mx"}

        payload = {
            "citySlug": "mexico-city-df",
            "category": "american",
            "pageNumber": page
        }
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "priority": "u=1, i",
            "referer": f"https://www.ubereats.com/mx/category/mexico-city-df/american?page={page}",
            "sec-ch-prefers-color-scheme": "dark",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "x-csrf-token": "x",
            "x-uber-ciid": "41270843-4fc3-4122-bd5c-41d47edace67",
            "x-uber-client-gitref": "bd7681663ce1c75fe98231630f5e575b336e542d"
        }
        logger.info(f"SCRAPEANDO PÁGINA: {page}")

        response = RequestHandler.do_request(method="POST",url=url, body=payload, headers=headers, params=querystring)

        data = response.json()["data"]

        if page<=data["totalPages"]:
            return data["storesMap"]
        return
    

    def _get_store_ids(self):
        current_page = 1
        kfc_store_ids = []
        while current_page<=500:
            stores = self._get_stores_by_page(current_page)
            if not stores:
                break

            for key,value in stores.items():
                if value["title"].casefold().startswith("kfc") and self.city.casefold() in value["location"]["formattedAddress"].casefold():
                    kfc_store_ids.append(key)
                    
            current_page += 1
        return kfc_store_ids
    

    def _get_delivery_data(self,store_id, user_location):
        url = f"{self.base_url}/_p/api/getStoreV1"

        querystring = {"localeCode":"mx"}

        payload = {
            "storeUuid": store_id,
            "diningMode": "DELIVERY",
            "time": {"asap": True},
            "cbType": "EATER_ENDORSED"
        }
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.ubereats.com",
            "priority": "u=1, i",
            "referer": "https://www.ubereats.com/mx/store/kfc-cetram-1322/s2aF3lZuQy-vUDNnsE5-mQ?surfaceName=",
            "sec-ch-prefers-color-scheme": "dark",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "x-csrf-token": "x",
            "x-uber-ciid": "0436f803-05f2-4e30-bac2-23c354af08ba",
            "x-uber-client-gitref": "bd7681663ce1c75fe98231630f5e575b336e542d",
            "x-uber-request-id": "40959d65-ead5-45da-ab6f-0fa6e732cfa3",
            "x-uber-session-id": "46daddd0-2af8-41ca-ac8e-f163d2829949",
            "x-uber-target-location-latitude": str(user_location["lat"]),
            "x-uber-target-location-longitude": str(user_location["lng"]),
            "Cookie":"""uev2.id.xp=137f09fb-ac99-4b58-9382-cf54b9ee1ed3; dId=2671340f-305f-4339-b36b-8c0081fe17e7; _ua={"session_id":"fb108d1c-b161-49b0-9e9e-6ffd8f0890c5","session_time_ms":1774117557997}; marketing_vistor_id=f5c8e83f-0f21-47fb-ba5b-9bd7746e40f4; uev2.embed_theme_preference=dark; g_state={"i_l":0,"i_ll":1774117562854,"i_b":"VtRY3HAAG6AIbZh3z2pNLTIRYgrGcX3FR0bjX0vlB/I","i_e":{"enable_itp_optimization":0}}; cf_clearance=GeiZloSt2Wtc79FQUuNXkzNBRJGW07FrXnqnSq4Ie9Q-1774117582-1.2.1.1-vMQ4uM8l9svHX0ARPoJU2iXPoA2kSKQP_RDLGKDCqtL_kUSy6nrjGHdpRn0isKXHicJ7EbcKpTbCd5hPbSzbBHvOuqbU21lM5ftcvlQ7mbswp56bbA8qYk1o4.C1AeXoh0kFPkKF7GSLuyqTdCGgdc5fiLdG0VBjwUR7q_xL5BzVg1HG067Yh.SI0vjUci0YLJSLeb778zcwdtPEw9xrqG9LhTVp_xjcECGk4.usLFU; u-cookie-prefs=eyJ2ZXJzaW9uIjoxMDAsImRhdGUiOjE3NzQxMTc2MTM0MjUsImNvb2tpZUNhdGVnb3JpZXMiOlsiZXNzZW50aWFsIl0sImltcGxpY2l0IjpmYWxzZX0%3D; uev2.gg=false; utm_medium=undefined; utm_source=undefined; uev2.diningMode=DELIVERY; sid=QA.CAESEM7svrQiF0Hgn8KInwSmjv4Y8NWx1QYiATEqJDBmMDU5ZDZhLWUxNzgtNDU2Yy1iODVkLWNiMmZkMWQ3Yjg1YjI81MZk0EqqpaGkkK-6272oB6aucMgTG7Vzi1iGZ9myWXtz232tyIffyfPTu_eVrp6y3ukj8p50H_JYfyN1OgExQg0udWJlcmVhdHMuY29t.hfB5zrEvF5pywBe7ZQOVvW-7iCy9dY3m53IRtWeG9kk; smeta={expiresAt:1789684464200}; udi-id=z0fBIjio5b0MkY9WIMxiDlgprCE88PXKUibOrti9noltdV6d9BeY3CYQ4DUKFOW8USxZ8ZwwY389hwL3h9cvukfEbNjsdtEjBlxCEuZ8n38tQWHZJPsK0uWUVDx9uXeRKQ2jiEBRuF21/wijvwwdml7+sAfIw0yKOSUlBFvRJPzfet4ibdc86wwVAWPL2FI8DqY0kVG1v8wIgog+CoMnjw==gPxfuHFUMpAoLWWl2ylEqg==GcJ3I3uvTeON5SsYGelQGUhmhxML3WS0DydkRnAZ1gY=; uev2.loc=%7B%22address%22%3A%7B%22address1%22%3A%22Plaza%20de%20la%20Constituci%C3%B3n%22%2C%22address2%22%3A%22Pl.%20de%20la%20Constituci%C3%B3n%2C%20Centro%20Hist%C3%B3rico%20de%20la%20Cdad.%20de%20M%C3%A9xico%2C%20Centro%2C%20Ciudad%20de%20M%C3%A9xico%2C%20CDMX%22%2C%22aptOrSuite%22%3A%22%22%2C%22eaterFormattedAddress%22%3A%22Pl.%20de%20la%20Constituci%C3%B3n%2C%20Centro%20Hist%C3%B3rico%20de%20la%20Cdad.%20de%20M%C3%A9xico%2C%20Centro%2C%20Ciudad%20de%20M%C3%A9xico%2C%20CDMX%2C%20M%C3%A9xico%22%2C%22subtitle%22%3A%22Pl.%20de%20la%20Constituci%C3%B3n%2C%20Centro%20Hist%C3%B3rico%20de%20la%20Cdad.%20de%20M%C3%A9xico%2C%20Centro%2C%20Ciudad%20de%20M%C3%A9xico%2C%20CDMX%22%2C%22title%22%3A%22Plaza%20de%20la%20Constituci%C3%B3n%22%2C%22uuid%22%3A%22%22%7D%2C%22latitude%22%3A19.4333514%2C%22longitude%22%3A-99.1332634%2C%22reference%22%3A%22EmpQbC4gZGUgbGEgQ29uc3RpdHVjacOzbiwgQ2VudHJvIEhpc3TDs3JpY28gZGUgbGEgQ2RhZC4gZGUgTcOpeGljbywgQ2VudHJvLCBDaXVkYWQgZGUgTcOpeGljbywgQ0RNWCwgTWV4aWNvIi4qLAoUChIJh9f3Rs3-0YURMWwnedIYyrESFAoSCb1NDi4t-dGFET2JxECndFWQ%22%2C%22referenceType%22%3A%22google_places%22%2C%22type%22%3A%22google_places%22%2C%22addressComponents%22%3A%7B%22city%22%3A%22M%C3%A9xico%20D.F.%22%2C%22countryCode%22%3A%22MX%22%2C%22firstLevelSubdivisionCode%22%3A%22CDMX%22%2C%22postalCode%22%3A%22%22%7D%2C%22categories%22%3A%5B%22route%22%2C%22street%22%2C%22segment%22%5D%2C%22originType%22%3A%22user_autocomplete%22%2C%22residenceType%22%3A%22OTHER%22%7D; uev2.id.session_v2=48f9975b-b2e6-41b1-acd9-0aafb1af72cc; uev2.ts.session_v2=1774214701547; uev2.id.session=46daddd0-2af8-41ca-ac8e-f163d2829949; uev2.ts.session=1774215189416; utag_main__sn=5; utag_main_ses_id=1774215361383%3Bexp-session; utag_main__ss=0%3Bexp-session; __cf_bm=vOqcVSKL1d1ZxGsszy1cUru.25SQuoV0177RLmwz.Nw-1774216789-1.0.1.1-Uhu_zFyZztRrT9abfcdsP3hLvD2fXopUxfMpl_yT1DP86i8CF7n7txD0Yz7DW5ZUzd3AWvsy2QryKlEVUsTnTndsFbFHimOUy6CaUj6Wd5M; jwt-session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NzQyMDM5NzYsImRhdGEiOnsic2xhdGUtZXhwaXJlcy1hdCI6MTc3NDIxODgxMzcxOX0sImV4cCI6MTc3NDI5MDM3Nn0.HSQdiRrbTMql9Xm9fzfvUIX9wMShsRefM75opfAawew; mp_adec770be288b16d9008c964acfba5c2_mixpanel=%7B%22distinct_id%22%3A%20%220f059d6a-e178-456c-b85d-cb2fd1d7b85b%22%2C%22%24device_id%22%3A%20%2219d11a5a94af11-00f29fa91ee283-12462c6e-232800-19d11a5a94b211b%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22%24user_id%22%3A%20%220f059d6a-e178-456c-b85d-cb2fd1d7b85b%22%7D; utag_main__pn=5%3Bexp-session; _userUuid=0f059d6a-e178-456c-b85d-cb2fd1d7b85b; utag_main__se=15%3Bexp-session; utag_main__st=1774218964834%3Bexp-session"""
        }
        response = RequestHandler.do_request(method="POST",url=url, body=payload, headers=headers, params=querystring)

        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise Exception(f"Ocurrió un error buscando datos de store: {store_id}  | Error: {response.text}| status code: {response.status_code}")


    def _extract_eta_cost(self,text:str)->int:
        match = re.search(r"MXN(\d+)", text)

        if match:
            return int(match.group(1))
        
    def _from_minutes_to_time(self,minutes):
        hours = (minutes // 60) % 24
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:00"
    

