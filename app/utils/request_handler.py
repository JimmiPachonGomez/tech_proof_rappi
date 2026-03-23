import requests
from .sync_retry import sync_retry  
from .logger import logger


class RequestHandler:

    @sync_retry()  
    @staticmethod
    def do_request(method, url, headers=None, body=None, params=None, data=None, timeout=20000):
        logger.info(f"Iniciando petición {method} a {url}")

        response = requests.request(
                                    method=method,
                                    url=url,
                                    headers=headers,
                                    json=body,
                                    params=params,
                                    timeout=timeout,
                                    data=data
                                    )

        logger.info(f"Status de respuesta: {response.status_code}")

        if response.status_code != 404:
            response.raise_for_status()
            
        if response.status_code in [200,404]:
            return response

        
        
        