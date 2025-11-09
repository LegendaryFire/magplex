# MagPlex 
A web-based Stalker player and STB portal client emulator designed to replace your Mag device with Plex Live TV and Jellyfin.

Features include electronic program guide (EPG) synchronization, interval-based refreshing, and more. The included live player lets you watch channels directly through the web interface.

## Configuration
### Requirements
You will need your Mag box `DEVICE_ID`, `DEVICE_ID2` and `SIGNATURE` depending on the provider. These can be obtained by sniffing the network traffic between your set top box and the portal. 
The devices `MAC_ADDRESS` is also needed, and can be found physically on the bottom of the device.

### Example `docker-compose.yml`
```
services:
  redis:
    image: redis
    container_name: redis
    restart: unless-stopped

  postgres:
    image: postgres:17
    container_name: postgres
    shm_size: 128mb
    environment:
      - POSTGRES_USER=username
      - POSTGRES_PASSWORD=password
    restart: unless-stopped

  magplex:
    image: magplex
    container_name: magplex
    ports:
      - 8080:8080
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=username
      - POSTGRES_PASSWORD=password
    depends_on:
      - redis
      - postgres
    volumes:
      - ./media/magplex/logs:/logs
    restart: unless-stopped
```

### Optional Environment Variables
| Variable       | Default                    | Description                                                       |
|:---------------|:---------------------------|:------------------------------------------------------------------|
| FFMPEG         | Automatic                  | Path to your FFMPEG executable                                    |
| CODEC          | Remux                      | The FFMPEG codec for HDHomeRun *(remux not recommended)*          |

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

### Initial Setup
MagPlex exposes it's web portal on port 8080, which is used to configure your device. The default login credentials are admin for the username, and admin for the password. It's **highly** recommended you change these to something more secure.

Your username and password can be updated by navigating to `Settings → Change Username`, and `Settings → Change Password` respectively. Once you've updated your credentials, you can add your device in `Settings → Device Configuration`.

Once your device has been added, allow a minute or so for MagPlex to pull your providers channel playlist. Navigating back to the home page, you should see a list of all channels which are ready to be played.

It's also strongly recommended to run MagPlex behind a reverse proxy, preferrably through HTTPS. This is also required for integration with Plex and Jellyfin. See integration with Plex and Jellyfin for more information.

## Integrating with Plex and Jellyfin
All required endpoints are authenticated using either a session or API key. This was done to prevent unauthorized access to a users device for those who only wish to use the web player. With that
being said, it adds a layer of complexity to integrating with Plex and Jellyfin. Since there's no way to add headers to the requests coming from Plex or Jellyfin, we must use a reverse proxy 
to inject the `X-Device-Uid` and `X-Api-Key` headers when requests are made to MagPlex.

The other reason a reverse proxy is required is to prevent conflict between the HDHomeRun endpoints, and the web portal endpoints. Plex and Jellyfin expect the HDHomeRun endpoints to exist at certain URL paths. MagPlex uses an internal nginx 
instance to rewrite the URL's and forward any network requests sent to port 34400 to `/api/<device_uid>/stb`. 

The configuration below assumes nginx is running in docker, on the same docker network as the other containers as they are accessible through container name opposed to IP addresses. Ensure ports 8080 and 34400 are mapped on your nginx docker 
configuration and remove port 8080 from MagPlex (if using example Docker compose file). If you're adding to an existing Docker compose file, ensure they are using a bridge network to access containers by container name. To get the Device UID
and API key, visit `Settings → API Key`.

Once you have your nginx instance running, we can now go ahead and add your device to Plex and/or Jellyfin. Typically, Plex should detect MagPlex upon adding a HDHomeRun device. When prompted about a channel guide, click the `Have an XMLTV
Channel Guide` button and enter `http://server-ip:34400/guide.xml` or `https://server-ip:34400/guide.xml` if you configured TLS certificates.

#### Example Nginx and Docker Configuration
##### docker-compose.yml
```
services:
  nginx:
    image: nginx:latest
    container_name: nginx
    depends_on:
      - magplex
    ports:
      - "8080:8080"
      - "34400:34400"
    volumes:
      # Mount your Nginx config file here.
      - ./network/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro

      # Optional: add a logs directory to view access/error logs locally
      - ./media/nginx/logs:/var/log/nginx
    restart: unless-stopped

  redis:
    image: redis
    container_name: redis
    restart: unless-stopped

  postgres:
    image: postgres:17
    container_name: postgres
    shm_size: 128mb
    environment:
      - POSTGRES_USER=username
      - POSTGRES_PASSWORD=password
    restart: unless-stopped

  magplex:
    image: magplex
    container_name: magplex
    ports:
      - 8080:8080
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=username
      - POSTGRES_PASSWORD=password
    depends_on:
      - redis
      - postgres
    volumes:
      - ./media/magplex/logs:/logs
    restart: unless-stopped
```

##### nginx.conf
```
server {
    listen 8080;
    server_name _;

    location / {
        proxy_pass http://magplex:8080;

        # Pass through the original host and client IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Forward other common proxy headers
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 34400;
    server_name _;

    location / {
        proxy_pass http://magplex:34400;

        # Pass through original host and client IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Add authentication headers required by MagPlex
        proxy_set_header X-Api-Key "INSERT_API_KEY";
        proxy_set_header X-Device-Uid "INSERT_DEVICE_UID";

        # Forward other common proxy headers
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```


## Endpoints
### REST API Endpoints
All endpoints respond with JSON unless specified otherwise. The Content-Type header must be set to `application/json` for any POST requests.

Certain endpoints, such as channel playback or proxy routes, may return an HTTP redirect or stream instead. Query parameters can be used to refine results, and optional parameters can be omitted.
Each request must includes a `device_uid` path parameter to specify the target device. The channel proxy endpoint is primarily used to prevent CORS errors when streaming over the web portal.

Each endpoint must be authenticated by setting the X-Api-Key header with the users API key, a key can be generated by visiting `Settings → API Key`. Both Plex and Jellyfin expect to see a HDHomeRun
device using particular URL routes. To avoid conflict of routes between the web player and STB, MagPlex utilized nginx to rewrite HDHomeRun endpoint routes to their cooresponding MagPlex endpoints.

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
| `GET`     | `is_completed` *(bool, optional)*                               | Returns the four most recent background tasks and their completion<br>statuses filtered from query parameters.  |


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
