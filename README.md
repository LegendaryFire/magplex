# MagPlex 
A web based interpeter and stalker portal emulator to integrate your Mag STB with Plex Live TV. Support for electronic program guide updates, interval refreshing and more.

### Requirements
You will need your Mag box `DEVICE_ID`, `DEVICE_ID2` and `SIGNATURE`. These can be obtained by sniffing the network traffic between your set top box and the portal.

### Setting up the EPG
Most portals do not have an endpoint to retreive the electronic program guide for every channel at once, so each channels EPG is pulled separately. The EPG data is cached to prevent being rate limited and reduce load on the portal server. 

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
