import socket
import json
import requests
import base64
import asyncio

async def read_adsb_data():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("10.0.10.34", 30154))
        while True:
            packet = socket.SocketIO(s, "r").readline()
            json_packet = json.loads(packet)
            # print(json_packet)
            if json_packet.get("r_dst", 100) < 300:
                print("Aircraft nearby!!!!")
                print(json.dumps(json_packet, indent=2))
                photo_response = requests.get("https://api.planespotters.net/pub/photos/hex/A009A4")
                if photo_response.ok:
                    photo_info = json.loads(photo_response.content)
                    if len(photo_info.get("photos", [])) > 0:
                        photo_response = requests.get(photo_info.get("photos", [{}])[0].get("thumbnail_large", {}).get("src", ""))
                        if photo_response.ok:
                            print(base64.b64encode(photo_response.content))


