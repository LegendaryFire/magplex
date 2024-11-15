# MagPlex 
A web based interpeter and stalker portal emulator to integrate your Mag STB with Plex Live TV. Support for electronic program guide updates, interval refreshing and more.

### Requirements
You will need your Mag box `DEVICE_ID`, `DEVICE_ID2` and `SIGNATURE`. These can be obtained by sniffing the network traffic between your set top box and the portal.

### Setting up the EPG
Most portals do not have an endpoint to retreive the electronic program guide for every channel at once, so each channel EPG is pulled individually. The data is cached to prevent rate limiting and reduce load on the portal server. Recommended cache expiration for the guide is thirty minutes. The Plex EPG is refreshed every twenty-four hours by default. To force a more frequent updates, specify the Plex API token, server address, DVR ID and refresh time in the environment variables.

### Example `docker-compose.yml`
```
services:
  magplex:
    image: magplex
    container_name: magplex
    ports:
      - 5123:5123
    environment:
      - PORTAL=PORTAL_DOMAIN
      - MAC_ADDRESS=MAC_ADDRESS
      - STB_LANG=en
      - TZ=Etc/UTC
      - DEVICE_ID=DEVICE_ID
      - DEVICE_ID2=DEVICE_ID2
      - SIGNATURE=SIGNATURE
      - CACHE_EXPIRATION=SECONDS
      # - PLEX_SERVER=SERVER_IP:PORT
      # - PLEX_TOKEN=TOKEN
      # - PLEX_DVR=DVR_ID
      # - PLEX_REFRESH=SECONDS
    volumes:
      - ./media/magplex/logs:/logs
    restart: unless-stopped
```

### Setup and Endpoints
The channel list and channel guide data can be loaded into Threadfin by using the endpoints found below. It is reccommended to set up the proper filters and mapping before adding Threadfin to Plex.

| Endpoint                 | Link                                        |
|:------------------------:|:-------------------------------------------:|
| Channel List             | http://server-ip:5123/channel_list.m3u8     |
| XMLTV EPG                | http://server-ip:5123/channel_guide.xml     |

Server logs are displayed in the console, and also saved to `./logs/app.log`.
