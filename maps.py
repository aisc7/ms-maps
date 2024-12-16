from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# URL del microservicio de negocio
BUSINESS_MICROSERVICE_URL = "http://localhost:3333/vehiculos"

# Endpoint para actualizar la posición del vehículo
@app.route('/vehiculos/actualizar-posicion', methods=['PUT'])
def actualizar_posicion():
    datos = request.json

    # Validar datos requeridos
    vehiculo_id = datos.get("vehiculoId")
    latitud_inicial = datos.get("latitudInicial")
    longitud_inicial = datos.get("longitudInicial")
    latitud_final = datos.get("latitudFinal")
    longitud_final = datos.get("longitudFinal")

    # Validar que los campos obligatorios estén presentes
    if not vehiculo_id or latitud_inicial is None or longitud_inicial is None:
        return jsonify({"error": "vehiculoId, latitudInicial y longitudInicial son requeridos"}), 400

    # Crear el payload para enviar al ms-business
    payload = {
        "vehiculoId": vehiculo_id,
        "latitudInicial": latitud_inicial,
        "longitudInicial": longitud_inicial,
        "latitudFinal": latitud_final,
        "longitudFinal": longitud_final,
    }

    try:
        # Hacer la solicitud PUT al microservicio de negocio
        respuesta = requests.put(
            f"{BUSINESS_MICROSERVICE_URL}/actualizar-posicion",
            json=payload
        )
        respuesta.raise_for_status()
        return jsonify({
            "message": f"Posición del vehículo {vehiculo_id} actualizada exitosamente.",
            "data": respuesta.json()
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Error al comunicarse con el microservicio de negocio.",
            "details": str(e)
        }), 500

# Endpoint para obtener la lista de vehículos con sus posiciones actuales
@app.route('/vehiculos', methods=['GET'])
def obtener_vehiculos():
    try:
        # Solicitar la lista de vehículos y sus posiciones actuales al ms-business
        respuesta = requests.get(f"{BUSINESS_MICROSERVICE_URL}/posiciones")
        respuesta.raise_for_status()
        return jsonify(respuesta.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Error al obtener los datos de los vehículos.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
