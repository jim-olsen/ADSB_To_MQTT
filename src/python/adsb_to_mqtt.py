import json
import base64
import asyncio
import aiohttp
import logging
import time
import threading
import paho.mqtt.client as mqtt

logger = logging.getLogger('adsb_to_mqtt')

# Distance in nautical miles in which a plane must pass to be published
MAX_DISTANCE = 3
# readsb.service connection address and port
READ_ADSB_SERVICE_ADDR = "10.0.10.34"
READ_ADSB_SERVICE_PORT = 30154
# MQTT server address, port, and topic
MQTT_SERVER_ADDR = "10.0.10.31"
MQTT_SERVER_PORT = 1883
MQTT_TOPIC = "adsb"

# The mqtt client established in its own thread
MQTT_CLIENT = None

#
# Given we have an adsb packet from a plane within range, attempt to get an image of the plane to add to the adsb
# json record and uuencode it into the json record.  Once a record is retrieved, or if no image is available, publish
# the ADSB information to the MQTT server in the configured topic.
# PARAMETERS
#       json_packet - The json formatted ADSB information from the readsb service
#
async def handle_adsb_packet(json_packet):
    global MQTT_CLIENT

    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get("https://api.planespotters.net/pub/photos/hex/" + json_packet.get("hex", "")) as http_response:
                photo_response = await http_response.json()
                if len(photo_response.get("photos", [])) > 0:
                    async with http_session.get(photo_response.get("photos", [{}])[0].get("thumbnail_large", {}).get("src", "")) as photo_response:
                        photo = await photo_response.read()
                        uuencoded_photo = base64.b64encode(photo)
                        json_packet["picture"] = uuencoded_photo.decode('ascii')
                        logger.info(json.dumps(json_packet, indent=2))
    except Exception as e:
        logger.error(f"Failed to fetch picture of aircraft: {e}")

    MQTT_CLIENT.publish(MQTT_TOPIC, json.dumps(json_packet))


#
# Connect to the readsb.service json port instance and read all records as the come in.  When we find an aircraft
# within range, asynchronously enrich the record with a photo of the aircraft and publish to the MQTT queue.
#
async def read_adsb_data():
    global READ_ADSB_SERVICE_ADDR, READ_ADSB_SERVICE_PORT
    reader, writer = await asyncio.open_connection(READ_ADSB_SERVICE_ADDR, READ_ADSB_SERVICE_PORT)
    complete_packet = ""
    async for packet in reader:
        try:
            complete_packet += packet.decode('ascii')
            if complete_packet.endswith("}\n"):
                json_packet = json.loads(complete_packet)
                complete_packet = ""
                if json_packet.get("r_dst", 100) < MAX_DISTANCE:
                    logger.info("Aircraft nearby!!!!")
                    asyncio.create_task(handle_adsb_packet(json_packet))
        except Exception as e:
            logger.error(f"Failed to process packet: {e}")

#
# Startup the mqtt client and register callbacks to reconnect on any client disconnections
#
def start_mqtt_client():
    global MQTT_SERVER_ADDR, MQTT_CLIENT, MQTT_SERVER_PORT

    def on_connect(c, userdata, flags, rc):
        global MQTT_CLIENT

        logger.info("MQTT Client Connected")
        MQTT_CLIENT = c

    def on_disconnect(c, userdata, rc):
        logger.info(f"MQTT Client Disconnected due to {rc}, retrying....")
        while True:
            try:
                c.reconnect()
                break
            except Exception as e:
                logger.error(f"Failed to reconnect: {e}, will retry....")
            time.sleep(30)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(MQTT_SERVER_ADDR, MQTT_SERVER_PORT, 60)
    client.loop_forever()

#
# Configure the logger to the desired logging level, start an MQTT client thread for publishing data and maintaining
# the connection to the server and connect and process packets from the readsb service
#
def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger.info("Starting MQTT Thread")
    mqtt_thread = threading.Thread(target=start_mqtt_client, args=())
    mqtt_thread.daemon = True
    mqtt_thread.start()

    logger.info("Starting Communications Event Loop")
    asyncio.run(read_adsb_data())

if __name__ == "__main__":
    main()


