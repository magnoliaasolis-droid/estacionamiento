import requests

url = "https://estacionamiento-1-3dlw.onrender.com/sensor"

# Cambia entre entrada o salida
datos = {
    "tipo": "entrada",
    "distancia": 4
}

respuesta = requests.post(url, json=datos)

print("Respuesta servidor:")
print(respuesta.text)