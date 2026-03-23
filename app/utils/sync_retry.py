from functools import wraps
from .logger import logger
import time


def sync_retry(times:int = 4, delay:float = 20.0, backoff: float = 2.0):
    """
    Decorador síncrono para reintentar una función en caso de error.

    Parámetros:
        times: Número de veces que se debe intentar
        delay: Tiempo de espera en cada intento
        backoff: Multiplicador de espera en cada intento
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.error(f"Intento {attempt}/{times} fallido: {e}")
                    
                    if attempt < times:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator