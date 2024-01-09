# ADSB to MQTT Publisher

This python program is a simple program to read traffic from the json port of a ADSB tracker such as that provided
by running an ADSBExchange raspberry pi image.  It communicates with the readsb.service to get json records about
any aircraft within a configured distance of the receiving station.

To find the port it is publishing on, utilize:

```
sudo systemctl status readsb.service
```

and you will get back something like:

```
readsb.service - readsb ADS-B receiver
     Loaded: loaded (/etc/systemd/system/readsb.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2024-01-08 04:00:07 MST; 10h ago
       Docs: https://github.com/mictronics/readsb
   Main PID: 471 (readsb)
      Tasks: 11 (limit: 3720)
        CPU: 1h 17min 19.089s
     CGroup: /system.slice/readsb.service
             └─471 /usr/bin/readsb --net-api-port 30152 --net-json-port 30154 --write-prom /run/readsb/stats.pr>
Jan 08 04:00:07 adsbexchange readsb[471]: 30154: Position json output port
Jan 08 04:00:07 adsbexchange readsb[471]: 30003: SBS TCP output ALL port
Jan 08 04:00:07 adsbexchange readsb[471]: 30001: Raw TCP input port
Jan 08 04:00:07 adsbexchange readsb[471]: 30004: Beast TCP input port
Jan 08 04:00:07 adsbexchange readsb[471]: 30104: Beast TCP input port
Jan 08 04:00:07 adsbexchange readsb[471]: 30152: API output port
```

the --net-json-port is the one that this script wants to connect to.

The script will connect to the specified MQTT server and send any received ADSB packets to the MQTT server.  It
further enhances these packets by adding in a photo of the plane from plane spotters API so that an image of the
approaching aircraft can be displayed.

## Configuration Items

MAX_DISTANCE - The distance in nautical miles within which a plane must pass before publishing the data<br/>
READ_ADSB_SERVICE_ADDR - The IP address of the adsb tracker<br/>
READ_ADSB_SERVICE_PORT - The port on which the json service is attached to (see above)<br/>
MQTT_SERVER_ADDR - The IP address of the MQTT server to publish packets to<br/>
MQTT_SERVER_PORT - The port on which the MQTT server is listening<br/>
MQTT_TOPIC - The topic on which the results should be published<br/>

