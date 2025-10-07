# MagPlex 
A web based interpeter and stalker portal emulator to integrate your Mag STB with Plex Live TV. Support for electronic program guide updates, interval refreshing and more.
## Configuration
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
    volumes:
      - ./media/magplex/logs:/logs
    restart: unless-stopped
```
#### Optional Environment Variables
| Variable       | Default          | Description                        |
|:---------------|:-----------------|:-----------------------------------|
| REDIS_HOST     | Automatic        | Hostname to your redis instance    |
| REDIS_PORT     | Automatic        | Port to your redis instance        |
| FFMPEG         | Automatic        | Path to your FFMPEG executable     |
| CODEC          | Remux            | The FFMPEG codec for the STB.      |

#### Available Codecs
The FFMPEG stream used by the HDHomeRun endpoint is only remuxed by default. Avoid using software encoding unless absolutely mandatory.
| Codec       | Description                           |
|:------------|:--------------------------------------|
| remux       | No encoding (default)                 |
| libx265     | Software Encoding                     |
| hevc_qsv    | Intel QuickSync                       |
| hevc_nvenc  | Dedicated Nvidia GPU                  |
| hevc_amf    | Dedicated AMD GPU                     |

### Device Specific Configuration
#### Intel Quick Sync
Support for Intel Quick Sync requires a Intel CPU integrated GPU with H265 encoding support. Minimum supported CPUs are Intel Kaby Lake 7th generation processors. To add support for Quick Sync, simply add your integrated GPU device to your docker compose.
```
devices:
  - "/dev/dri:/dev/dri"
```

#### Nvidia Encoder (NVENC)
Support for NVENC requires a Nvidia GPU with an H265 encoding support. Minimum supported GPUs are the Nvidia GTX 10xx series.
```
gpus: "all"
environment:
  - NVIDIA_DRIVER_CAPABILITIES=video
```

<br>

## Endpoints
### REST API Endpoints
This is used for getting raw JSON data from your device.
| Name                     | Port  | Endpoint                      |
|:-------------------------|:------|:------------------------------|
| Channel List             | 8080  | /api/channels/list            |
| Channel Playlist         | 8080  | /api/channels/stream_id       |


### Proxy Endpoints
The following endpoints are proxied through the server and primarily used by the web portal. Channel streams are located at a different domain, so these endpoints are proxied to avoid CORS errors.
| Name                     | Port       |Endpoint                          |
|:-------------------------|:-----------|:---------------------------------|
| Channel Playlist         | 8080/34400 | /proxy/channels/stream_id        |
| Channel Segment          | 8080/34400 | /proxy/stream/?url=segment_url   |


### HDHomeRun Endpoints
The endpoints found below are primarily for use for Plex, and simulate an HDHomeRun device. Depending on your network, your device should be automatically recognized when configuring with Plex. 
| Name                     | Port  | Endpoint                |
|:-------------------------|:------|:------------------------|
| Device                   | 34400 | /                       |
| Discover                 | 34400 | /discover.json          |
| Lineup Status            | 34400 | /lineup_status.json     |
| Channel List             | 34400 | /lineup.json            |
| XML TV Guide             | 34400 | /channels/guide.xml     |
| Channel Stream           | 34400 | /channels/stream_id     |

Server logs are displayed in the console, and also saved to `./logs/app.log`.
