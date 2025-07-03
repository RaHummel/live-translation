<div align="center" xmlns="http://www.w3.org/1999/html">

<!-- logo -->
<p align="center">
  <img src="img/live-translation.png" width="300px" style="vertical-align:middle;">
</p>

<!-- Badges -->
<p align="center">
  
  <a href="https://github.com/RaHummel/live-translation/issues"><img src="https://img.shields.io/github/issues/RaHummel/live-translation.svg?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/RaHummel/live-translation/stargazers"><img src="https://img.shields.io/github/stars/RaHummel/live-translation.svg?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/RaHummel/live-translation/network/members"><img src="https://img.shields.io/github/forks/RaHummel/live-translation.svg?style=flat-square" alt="Forks"></a>
  <a href="https://github.com/RaHummel/live-translation/blob/main/LICENSE"><img src="https://img.shields.io/github/license/RaHummel/live-translation.svg?style=flat-square" alt="License"></a>
</p>
</div>
This project is a real-time translation service that captures audio input, translates it using a specified translator, and outputs the translated audio to a specified output device.

## Features

- **Real-time Translation**: Captures live audio input and translates it instantly.
- **Multiple Output Options**: Supports various output options, including Speaker and Mumble.
- **Customizable Translators**: Easily switch between different translation services like AWS.

## Architecture Overview

The following diagram shows how the recommended setup works.

<p align="center">
  <img src="img/architecture-diagram.png" style="vertical-align:middle;">
</p>

1. The input sound is transferred to the device running the translation service. This depends heavily on the conditions on-site and could involve multiple devices like an audio mixer, etc.
2. The translation service translates this input audio according to the configuration.  
    2a. Speech-to-Text: This service streams the input into AWS Transcribe. AWS Transcribe analyzes the audio, looks for end of sentences or pauses and returns pieces of text in the original language of the audio.  
    2b. Text-to-Text: The pieces of texts are sent to AWS Translate. AWS Translate returns the translation as text for every requested language.  
    2c. Text-to-Speech: The translated text is sent to AWS Polly. AWS Polly returns an audio file for each requested language.
3. This service is connected to the configured Mumble Server (once per language). The translated audio is then played in each respective channel. The device running this service and the mumble server may be identical.
4. The audience logs into the mumble service with their device (e.g. their Smartphone) and joins the channel of the language of their choice. For IOS use [Mumble](https://apps.apple.com/de/app/mumble/id443472808). For Android use [Mumla](https://play.google.com/store/apps/details?id=se.lublin.mumla&hl=de). If the Mumble Service runs in a local network, audience has to join the same network with their devices. E.g. if there is a local internet router devices have to connect to the local Wifi.


## Installation

How to install the translation service.

### Prerequisites

1. **Python 3.11+**
    - **Ubuntu**: Possible you need:
      ```bash
      sudo apt-get install python3-dev
      ```
2. **PortAudio**:
    - **Windows**: No specific installation required; `PyAudio` includes PortAudio binaries.
      ```bash
      pip install pyaudio
      ```
    - **Ubuntu**: Install PortAudio via package manager:
      ```bash
      sudo apt-get install portaudio19-dev/opus
      ```
      If you are on a armhf system (like Raspberry Pi OS), run:
      ```
      sudo apt-get install portaudio19-dev libopus-dev
      ```
    - **Mac OS X**: Install PortAudio using Homebrew:
      ```bash
      brew install portaudio
      ```
      
33. **Opus**:
    - **Windows**: Follow the [installation Guide](https://github.com/shardlab/discordrb/wiki/Installing-libopus#windows).
    - **Linux**: Install Opus (Arch Linux opus/lib32-opus) via package manager (not tested):
        ```bash
        sudo apt-get install libopus0
        ```
    - **Mac OS X**: Install Opus using Homebrew:
      ```bash
      brew install opus
      ```
      Then copy the Opus library to `/usr/local/lib/`:
      ```bash
      sudo mkdir -p /usr/local/lib
      sudo cp $(brew --prefix opus)/lib/libopus.* /usr/local/lib/
      ```
34. **pipenv**:
    ```bash
    pip install pipenv
    ```

### Local Development Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/RaHummel/live-translation.git
    cd live-translation
    ```

2. Create a virtual environment and install dependencies:
    ```sh
    pipenv install
    ```

### Bundling the Project

To bundle the entire project into a deployable package:
```sh
make bundle  // Linux, OS X
```

```
.\build.ps1 bundle // Windows
```

## Translators

### AWS Translator Setup

Follow the [AWS Setup Guide](./docs/AwsSetup.md)

### Supported Languages

Supported languages and voice configurations can be found in the AWS [Polly Documentation](https://docs.aws.amazon.com/polly/latest/dg/available-voices.html).

## Mumble Setup
For detailed instructions on setting up Mumble, refer to the [Mumble Setup Guide](./docs/MumbleSetup.md)

## Device Management

To help you identify and configure available audio input and output devices on your system, you can use the `list_devices.py` script located in the `src/helper` directory. This script lists all available devices, which you can then specify in the `config.json` file for the `inputDevice` and `outputDevice` settings.

### Listing Devices

1. Navigate to the `src/helper` directory:
    ```sh
    cd src/helper
    ```

2. Run the `list_devices.py` script:
    ```sh
    python list_devices.py
    ```

3. The script will output a list of all available audio devices. Use the device names from this list to configure your `config.json` file.

**Example output:**
```
Input Devices:
0. Microphone (Realtek Audio)
1. USB Microphone

Output Devices:
0. Speakers (Realtek Audio)
1. Headphones (USB Audio)
```

## Configuration

The configuration file is located at `res/config.json`. It allows you to set parameters for the translator, input, and output devices.

**Guide**
- **output**:  
  - **mumble**: connects the translation service to your Mumble server. It depends on your local setup. If you do not run Mumble on the same device then adapt **ipAddress** and **port**. The **languageChannelMapping** has to match the [channel structure](/docs/MumbleSetup.md#channel-structure).
  - **speaker**: Used for testing without Mumble.
- **translator**: Only supports aws right now
  - **aws**:
    - **region**: choose the aws region you want to connect to. eu-central-1 is Europe (Frankfurt). All regions can be found [here](https://docs.aws.amazon.com/de_de/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html).
    - **source_language**: define all languages that you might want to use as source. You use the key (text before colon) to [run the service](#usage). The value (text after colon) has to match the [language-code used by AWS Transcribe](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html).
    - **target_language**: define all languages that you mught want to use as target language. You use the key (text before colon) to [run the service](#usage).
      - **language_code**: the language code has to match the [one defined by Amazon Polly](https://docs.aws.amazon.com/polly/latest/dg/available-voices.html).
      - **voice_id**: per language code [Amazon Polly offers different voices](https://docs.aws.amazon.com/polly/latest/dg/available-voices.html).

**Example Configuration:**
```json
{
  "inputDevice": "default",
  "output": {
    "mumble": {
      "ipAddress": "localhost",
      "port": 64738,
      "languageChannelMapping": {
        "en": "Channel/Subchannel"
      }
    },
    "speaker": {
      "outputDevice": "default"
    }
  },
  "translator": {
    "aws": {
      "region": "eu-central-1",
      "source_language": {
        "de": "de-DE",
        "en": "en-US"
      },
      "target_language": {
        "en": {
          "language_code": "en-US",
          "voice_id": "Kendra"
        },
        "pl": {
          "language_code": "pl-PL",
          "voice_id": "Jacek"
        },
        "ru": {
          "language_code": "ru-RU",
          "voice_id": "Maxim"
        },
        "de": {
          "language_code": "de-DE",
          "voice_id": "Vicki"
        }
      }
    }
  }
}
```

## Usage
After extracting the bundled zip file to your desired location, run the translation service with the following command:
```sh
python main.py 
```

If you want to use it without bundling, then make sure to first activate the pipenv environment. Run the following in the live-translation folder:
```sh
pipenv shell
python src/main.py 
```

**Command-line Arguments**
- `-t, --translator`: Translator to use (default: aws)
- `-i, --input`: Sound input method to use (default: mic)
- `-o, --output`: Sound output method to use (default: mumble)
- `-sl, --source_lang`: Source language (default: de)
- `-tl, --target_lang`: Target language(s) (default: [en])


## Known Issues

- **Opuslib and pymumble**: These libraries are no longer maintained. Forked versions are used with necessary modifications.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
