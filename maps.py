import json
import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Habilitar CORS para permitir el acceso desde el frontend
CORS(app, origins="http://localhost:4200")

# URLs de los microservicios dependientes
BUSINESS_MICROSERVICE_URL = "http://localhost:3333"  # Microservicio de negocios
NOTIFICATIONS_MICROSERVICE_URL = "http://localhost:5000/send_email"  # Microservicio de notificaciones

# Cargar el JSON de coordenadas
def cargar_coordenadas_paises():
    try:
        ruta_paises = os.path.join(os.path.dirname(__file__), 'paises.json')
        with open(ruta_paises, 'r', encoding='utf-8') as archivo:
            paises = json.load(archivo)
        # Convertir a un diccionario para búsqueda rápida
        return {pais['nombre']: {'latitud': pais['latitud'], 'longitud': pais['longitud']} for pais in paises}
    except Exception as e:
        print(f"Error al cargar coordenadas de países: {e}")
        return {}

# Cargar coordenadas al inicio
COORDENADAS_PAISES = cargar_coordenadas_paises()

# Simular movimiento con las coordenadas (sin depuración adicional)
def simular_movimiento(starting_coordinates, ending_coordinates, cliente_email, vehiculo_id):
    try:
        if not starting_coordinates or not ending_coordinates:
            return

        lat_inicial = float(starting_coordinates['latitud_inicial'])
        lon_inicial = float(starting_coordinates['longitud_inicial'])
        lat_final = float(ending_coordinates['latitud_final'])
        lon_final = float(ending_coordinates['longitud_final'])

        pasos = 100
        delta_lat = (lat_final - lat_inicial) / pasos
        delta_lon = (lon_final - lon_inicial) / pasos

        # Simula el movimiento
        for i in range(pasos):
            lat_inicial += delta_lat
            lon_inicial += delta_lon
            time.sleep(0.1)  # Tiempo entre cada paso de la simulación

        # Cuando se termina el movimiento, se envía el correo de notificación
        subject = f"Entrega completada para el vehículo {vehiculo_id}"
        body_html = f"""
            <p>Estimado cliente,</p>
            <p>Su carga ha llegado al destino final.</p>
            <p>Ubicación final: Latitud {lat_final}, Longitud {lon_final}</p>
            <p>Gracias por utilizar nuestro servicio.</p>
        """

        # Crear la carga útil para la solicitud de envío de correo
        email_payload = {
            "subject": subject,
            "recipient": cliente_email,
            "body_html": body_html
        }

        # Enviar el correo al microservicio de notificaciones
        response = requests.post(NOTIFICATIONS_MICROSERVICE_URL, json=email_payload)

        if response.status_code == 200:
            print(f"Correo enviado exitosamente a {cliente_email}")
        else:
            print(f"Error al enviar el correo: {response.status_code}")

    except Exception as e:
        print(f"Error durante la simulación de movimiento: {e}")


# Endpoint para actualizar coordenadas
@app.route('/vehiculos/actualizar-coordenadas', methods=['PUT'])
def actualizar_coordenadas():
    try:
        # Extrae vehicle_id del cuerpo de la solicitud
        data = request.get_json()
        print(f"Datos recibidos: {data}")
        vehiculo_id = data.get('vehicle_id')

        if not vehiculo_id:
            return jsonify({"error": "vehicle_id es requerido"}), 400

        # Solicitar la ruta del vehículo
        url = f"{BUSINESS_MICROSERVICE_URL}/routes/by-vehicle/{vehiculo_id}"
        print(f"Solicitando URL: {url}")

        ruta_response = requests.get(url)
        ruta_response.raise_for_status()
        ruta_data = ruta_response.json()

        if not ruta_data:
            return jsonify({"error": "No se encontraron rutas"}), 404
        
        ruta = ruta_data[0]

        # Obtener lugares de inicio y fin
        starting_place = ruta.get('starting_place')
        ending_place = ruta.get('ending_place')

        # Buscar coordenadas de los lugares
        starting_coords = COORDENADAS_PAISES.get(starting_place, {})
        ending_coords = COORDENADAS_PAISES.get(ending_place, {})

        print(f"Coordenadas iniciales: {starting_coords}")
        print(f"Coordenadas finales: {ending_coords}")

        # Verificar si se encontraron coordenadas
        if not starting_coords or not ending_coords:
            return jsonify({
                "error": f"No se encontraron coordenadas para {starting_place} o {ending_place}"
            }), 404

        # Respuesta exitosa
        return jsonify({
            "message": "Coordenadas actualizadas exitosamente",
            "coordinates": {
                "latitud_inicial": starting_coords['latitud'],
                "longitud_inicial": starting_coords['longitud'],
                "latitud_final": ending_coords['latitud'],
                "longitud_final": ending_coords['longitud']
            }
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud: {e}")
        return jsonify({"error": f"Error al obtener datos de rutas: {str(e)}"}), 500
    except Exception as e:
        print(f"Error inesperado: {e}")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


# Endpoint para obtener posición (sin mensajes de depuración)
@app.route('/vehiculos/obtener-posicion', methods=['GET'])
def obtener_posicion():
    vehiculo_id = request.args.get("vehicle_id")

    if not vehiculo_id:
        return jsonify({"error": "vehicle_id es requerido"}), 400

    try:
        rutas_response = requests.get(f"{BUSINESS_MICROSERVICE_URL}/routes/by-vehicle/{vehiculo_id}")
        rutas_response.raise_for_status()
        rutas_data = rutas_response.json()

        if not rutas_data:
            return jsonify({"error": f"No se encontraron rutas para el vehicle_id {vehiculo_id}"}), 404

        ruta = rutas_data[0]
        contrato_id = ruta.get("contract_id")
        if not contrato_id:
            return jsonify({"error": f"La ruta con ID {ruta['id']} no tiene un contrato asociado."}), 404

        contrato_response = requests.get(f"{BUSINESS_MICROSERVICE_URL}/contracts/{contrato_id}")
        contrato_response.raise_for_status()
        contrato_data = contrato_response.json()

        cliente_id = contrato_data.get("customer_id")
        if not cliente_id:
            return jsonify({"error": f"El contrato con ID {contrato_id} no tiene un cliente asociado."}), 404

        cliente_response = requests.get(f"{BUSINESS_MICROSERVICE_URL}/customers/{cliente_id}")
        cliente_response.raise_for_status()
        cliente_data = cliente_response.json()

        vehiculo_response = requests.get(f"{BUSINESS_MICROSERVICE_URL}/vehiculos/{vehiculo_id}")
        vehiculo_response.raise_for_status()
        vehiculo_data = vehiculo_response.json()

        return jsonify({
            "vehiculoId": vehiculo_id,
            "contrato": contrato_data,
            "vehiculo": vehiculo_data,
            "cliente": cliente_data
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Error al comunicarse con el microservicio", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Error inesperado", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
