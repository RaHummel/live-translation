# Mumble Server Setup

## Installation
The Mumble server can nearly run on any Platform because it is lightweight and doesn't require much processing power. To facilitate future server setup and make it platform-independent, it runs in a dockerized environment. 

### Prerequisites
Ensure that Docker and Docker-Compose are installed on the system.

Next, create a `docker-compose.yml` and `.mumble-env` file in your desired directory with following content.
```
version: '3'
services:
  mumble-server:
    image: mumblevoip/mumble-server:latest
    container_name: mumble-server
    hostname: mumble-server
    restart: unless-stopped  // or on-failure
    ports:
      - "64738:64738/tcp"
      - "64738:64738/udp"
    volumes:
      - /path/to/directory:/data
    env_file:
      - .mumble-env

``` 
Replace /path/to/your/Mac/directory with the actual path where you want the data to be stored. This preserves your channel and ACL structure even if you update the Docker image.
See also official [Mumble Docker Image Code](https://github.com/mumble-voip/mumble-docker?tab=readme-ov-file)

```
MUMBLE_SUPERUSER_PASSWORD=
MUMBLE_CONFIG_allowping=true
MUMBLE_CONFIG_logdays=-1
MUMBLE_CONFIG_welcometext="<br /> Hello World</b>"
MUMBLE_CONFIG_registerName=My Mumble Server
```

The mumble-env file contains the parameters for the Mumble configuration. The parameters always start with the prefix MUMBLECONFIG and can include the parameters listed here as postfixes.

Before starting the container for the first time, set the MUMBLESUPERUSER__PASSWORD parameter to define a password for the SuperUser. Otherwise, a random password will be generated.

### Usage

Create and start the container with the following command:
```sh
docker-compose -f /path/to/your/docker-compose.yml pull
docker-compose -f /path/to/your/docker-compose.yml up -d
```

The container is configured to restart automatically after any reboot or in case of failure. To manually stop or start it, use the following commands:
```sh
docker stop mumble-server
docker start mumble-server
```

## Channel & ACL Configuration

### Channels and Permissions
Channels and permissions can only be configured with the SuperUser. When logging into the server, choose "SuperUser" as the username. A password prompt will then appear, corresponding to the password assigned to `MUMBLESUPERUSER__PASSWORD` in the `mumble-env` file.

### Channel Structure
The following channel structure can be taken as an example. Feel free to adjust it to your needs:
- **My Mumble Sever**
  - **German**
  - **English**
    - **Translator**
  - **Russian**
    - **Translater**
  - **Romanian**
    - **Translator**

At the top level is the `My Mumble Server` with the language channels as subchannels. Each language channel, except for the German one, has a **Translator** subchannel. In this example the German channel receives the **original input audio** from the speaker, which can be relayed to the translation channels if a manuall translation is required (This is optional!) . In the language channels themselves, only the audio from the underlying Translator can be heard.

### ACL (Permissions & Groups)
To make the language channels work as described above, appropriate ACLs must be defined. First, create a new group called e.g **master**. Assign the user which will provide the original audio to this group. This user must be registered beforehand.

Then set the following permissions for each channel:

- **My Mumble Server**
  - `@all` - Deny speak, deny whisper
- **German**
  - `@all` - Deny speak, deny whisper
  - `@master` - Allow speak, allow mute/deafen, deny whisper
- **English**
  - `@all` - Deny speak, deny whisper
  - `@~sub,0,1` - Allow speak
- **Russian**
  - `@all` - Deny speak, deny whisper
  - `@~sub,0,1` - Allow speak
- **Romanian**
  - `@all` - Deny speak, deny whisper
  - `@~sub,0,1` - Allow speak

**Note**: The Translator channels will get the default permissions. Permissions can be adjusted as needed.

Finally, link the channels by switching to each Translator channel as the SuperUser and linking it to the German channel and the one above it.
e.g from English/Translator channel
link to German and link to English
(Right-click on the channel -> Link).
