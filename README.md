# MagPlex 
A web-based Stalker player and STB portal client emulator designed to replace your Mag device with Plex Live TV and Jellyfin.

Features include electronic program guide (EPG) synchronization, interval-based refreshing, and more. The included live player lets you watch channels directly through the web interface.

## Configuration
### Requirements
You will need your Mag box `DEVICE_ID`, `DEVICE_ID2` and `SIGNATURE` depending on the provider. These can be obtained by sniffing the network traffic between your set top box and the portal. 
Device configuration can be edited under Settings, Device Configuration. The devices `MAC_ADDRESS` is also needed, and can be found physically on the bottom of the device.

### Example `docker-compose.yml`
```
services:
  redis:
    image: redis
    container_name: redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:17
    container_name: postgres
    shm_size: 128mb
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=username
      - POSTGRES_PASSWORD=password
    restart: unless-stopped

  magplex:
    image: magplex
    container_name: magplex
    ports:
      - 5123:5123
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=username
      - POSTGRES_PASSWORD=password
    volumes:
      - ./media/magplex/logs:/logs
    restart: unless-stopped
```

### Optional Environment Variables
| Variable       | Default          | Description                        |
|:---------------|:-----------------|:-----------------------------------|
| FFMPEG         | Automatic        | Path to your FFMPEG executable     |
| CODEC          | Remux            | The FFMPEG codec for the STB.      |

### Available Codecs
The FFMPEG stream is used by the HDHomeRun endpoints, and are remuxed by default. For Plex and Jellyfin integrations, hardware or software encoding is **strongly** recommended. Relying solely on remux can result in unreliable playback due to strict timing requirements in both platforms, particularly with mux delay and preload handling. When software or hardware encoding is enabled, all streams are re-encoded to H265.

| Codec       | Description                           |
|:------------|:--------------------------------------|
| remux       | No encoding (default)                 |
| libx265     | Software Encoding                     |
| hevc_qsv    | Intel QuickSync                       |
| hevc_nvenc  | Dedicated Nvidia GPU                  |
| hevc_amf    | Dedicated AMD GPU                     |


### GPU Specific Configuration
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
All endpoints respond with JSON unless specified otherwise. The Content-Type header must be set to `application/json` for any POST requests.

Certain endpoints, such as channel playback or proxy routes, may return an HTTP redirect or stream instead. Query parameters can be used to refine results, and optional parameters can be omitted.
Each request must includes a `device_uid` path parameter to specify the target device. The channel proxy endpoint is primarily used to prevent CORS errors when streaming over the web portal.

#### Genres → `/api/devices/<uuid:device_uid>/genres`
| Method    | Params                                                                         | Description                                                                     |
|:----------|:-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `GET`     | `channel_enabled` *(bool, optional)*<br>`channel_stale` *(bool, optional)*     | Returns a list of genres, with the applied<br>filters from query parameters.    |

#### Channels → `/api/devices/<uuid:device_uid>/channels`
| Method    | Params                                                                                                                                 | Description                                                                              |
|:----------|:---------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `GET`     | `channel_enabled` *(bool, optional)*<br>`channel_stale` *(bool, optional)*<br>`genre_id` *(int, optional)*<br>`q` *(str, optional)*    | Returns a list of all channels matching the applied<br> filters from query parameters.   |
| `POST`    | `channel_enabled` *(bool, optional)*                                                                                                   | Updates all channels enabled and stale status with<br>the value provided.                |

#### Channel → `/api/devices/<uuid:device_uid>/channels/<int:channel_id>`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns a redirect directly to the channel stream playlist.                   |
| `POST`    | `channel_enabled` *(bool, optional)*                            | Updates the channel enabled statuswith the value provided.                    |

#### Channel Refresh → `/api/devices/<uuid:device_uid>/channels/sync`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `POST`    | *No Parameters*                                                 | Triggers the update channel list background task to be ran immediately.       |

#### Channel Guides → `/api/devices/<uuid:device_uid>/channels/guides`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns a dictionary of all channel ID's and their channel guides.            |
| `POST`    | `channel_enabled` *(bool, optional)*                            | Updates the channel enabled statuswith the value provided.                    |

#### Channel Guide → `/api/devices/<uuid:device_uid>/channels/<int:channel_id>/guide`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns a list of all the specified channel ID's channel guides.              |

#### Channel Guide Refresh → `/api/devices/<uuid:device_uid>/channels/guides/sync`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `POST`    | *No Parameters*                                                 | Triggers the update channel guide background task to be ran immediately.      |

#### Channel Proxy → `/api/devices/<uuid:device_uid>/channels/<int:channel_id>/proxy`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns a redirect proxied to the channel stream playlist and segments.       |

#### Background Tasks → `/api/devices/<uuid:device_uid>/tasks`
| Method    | Params                                                          | Description                                                                                                     |
|:----------|:----------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `GET`     | `is_completed` *(bool, optional)*<br>                           | Returns the four most recent background tasks and their completion<br>statuses filtered from query parameters.  |
<br>

### HDHomeRun Endpoints
The endpoints found below are primarily for use for Plex and Jellyfin Live TV features, and are designed to simulate an HDHomeRun device. These endpoints primarily consist of XML and JSON.

#### Device → `/api/devices/<uuid:device_uid>/stb`
| Method    | Params                                                          | Description                                                                                                     |
|:----------|:----------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns the HDHomeRun device information as XML including the device name,<br>manufacture, model name and more. |

#### Discover → `/api/devices/<uuid:device_uid>/stb/discover.json`
| Method    | Params                                                          | Description                                                                                                                      |
|:----------|:----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns the HDHomeRun device information as JSON including the device name,<br>manufacture, model name, channel lineup and more. |

#### Lineup Status → `/api/devices/<uuid:device_uid>/stb/lineup_status.json`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns the HDHomeRun channel lineup status as JSON.                          |

#### Lineup → `/api/devices/<uuid:device_uid>/stb/lineup.json`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns the HDHomeRun channel list as JSON.                                   |

#### Channel Guides → `/api/devices/<uuid:device_uid>/stb/guide.xml`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | *No Parameters*                                                 | Returns the HDHomeRun channel guides in XML TV format.                        |

#### Channel Guides → `/api/devices/<uuid:device_uid>/stb/playlist.m3u8`
| Method    | Params                                                          | Description                                                                   |
|:----------|:----------------------------------------------------------------|-------------------------------------------------------------------------------|
| `GET`     | `stream_id` *(int, mandatory)*                                  | Returns a FFMPEG re-encoded video stream of the channels using the stream ID. |
