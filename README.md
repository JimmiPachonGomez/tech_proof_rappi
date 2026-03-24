# PRUEBA TÉCNICA PARA RAPPI (PARTE 1: SCRAPING)

## SETUP

Primero, clona este proyecto y accede a la carpeta principal:

```bash
git clone https://github.com/JimmiPachonGomez/tech_proof_rappi.git
```
Una vez clonado el proyecto copie y pegue los archivos '.env' y 'credentials.json' adjuntados por correo electrónico, si el archivo se llama 'env' renómbrelo a '.env'. Después de eso levante el entorno virtual e instale los requerimientos. Los siguientes comandos son para linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

En la carpeta 'scripts' están los archivos que ejecutan el scraping para cada empresa y hay uno que ejecuta los dos, para ejecutar el archivo 'scraping_total.py' ejecute el siguiente comando en la terminal:
```bash
python -m app.scripts.scraping_total
```

Debería empezar a ejecutarse el scraping para una localización de usuario que simula explorar todos los KFC de la ciudad. Al finalizar se envían los archivos a BigQuery pero también se generan dos archivos .json que contienen la información enviada, así puedes familiarizarte con la información recolectada.

## SCOPE
- Para esta prueba no llegué a la meta de dos competidores debido al poco tiempo que me quedaba, así que el scraping se realizó para Uber Eats y para Rappi.
- Me limité a estudiar una sola franquicia, elegí KFC por su popularidad y distribución por la ciudad.
- Sólo se estudió Ciudad de México.
- El script por defecto scrapea la información desde la localización de un usuario, sin embargo se puede configurar para scrapear más localizaciones ubicadas en el archivo 'locations.json'.
- Desconozco si el token de Rappi y la cookie de Uber Eats expira(es muy probable), sin embargo por tiempo no se cumplió con el objetivo de extraer esos datos con playwright y se dejaron como variables de entorno.
- Se extraen todos los productos encontrados.
- No desarrollé tests y monitoreo de errores debido al tiempo limitado.


## STACK
- Python (bs4, pydantic, requests)
- BigQuery (Es una base de datos especializada para analítica con precios muy convenientes y optimizada para grandes cantidades de datos)
- Looker (Se sincroniza bien con BigQuery y me pareció una buena solución para graficar rápidamente)
- Insomnia y Postman.

## COMENTARIOS TÉCNICOS Y CONCEPTUALES A MEJORAR EN EL PROYECTO
- No tengo una alarma de errores, en un caso real no tendría forma de saber si el script sigue funcionando.
- Las cookies y tokens generalmente expiran, se pueden obtener simulando un navegador con playwright.
- Didi tiene la complejidad de tener un sistema de seguridad que no permite alterar las peticiones, razón por la cual lo descarté del scope. Sin embargo con playwright y más tiempo seguramente lo solucionaba.
- Se podría desligar el proyecto de KFC y generalizarlo a más marcas y más ciudades.
- Se infirió el significado de algunos campos y no cumplí con verificar que cada uno se correspondiera con la realidad, puede haber inconsistencias por elegir mal algún dato como el Service Fee.
- Aplicar hilos con un manejo adecuado de errores para reducir el tiempo de ejecución.
- Realizar un dashboard o reporte mucho más elaborado y útil.

## DASHBOARD EN LOOKER
Puedes ver el dashboard yendo a este link: https://lookerstudio.google.com/reporting/469586bb-b966-4535-976e-21a1c09b5bee

## INSIGHTS
- En promedio Rappi promete menores tiempos de entrega, lo cuál es positivo cuando el usuario prioriza la inmediatez.
- Rappi maneja service fee por porcentaje, en cambio Uber Eats lo maneja con un costo fijo que varía acorde a un algoritmo. Se podría usar esto como una ventaja si se promueven muchas compras pequeñas o se puede contrarestar la estrategia de Uber con descuentos a compras grandes.
- Rappi tiene una ventaja territorial, con KFC se ve que tiene presencia en más establecimientos que Uber. Se podrían identificar los establecimientos y planear cómo ralentizar la expansión de Uber.
- Uber Eats juega mucho con los descuentos, aún así con un Service Fee y Costo de envío prudentes Rappi es más económico en el precio final. Debería analizarse cuál de las dos estrategias genera más tracción a nivel psicológico: ¿precio de producto aparentemente barato y otros costos más altos o precio más elevado y logística económica?
- Tendría que recolectar muchos más datos, pero todo apunta a que el radio de cobertura de un rappitendero es más amplio que el alcance de un repartidor de Uber. Esto juega un papel clave en horarios donde los repartidores son escasos.

## PARTE 2 DE LA PRUEBA TÉCNICA
Para tener acceso a la segunda parte, por favor contáctese conmigo por correo electrónico o por whatsapp dándome la lista de usuarios que requieren el acceso. Mi correo de contacto para eso es: jimmi.pachon2001@gmail.com .




