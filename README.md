# Translation Service

This project is a real-time translation service that captures audio input, translates it using a specified translator, and outputs the translated audio to a specified output device.

## Installation

### Pre-requisites

1. **Python 3.11+**
2. **PortAudio**:
    - For Ubuntu, you need to install the following packages: (not tested)
        ```bash
        sudo apt-get install portaudio19-dev
        ```
    - For Mac OS X, you need to install the following packages:
        ```bash
        brew install portaudio
        ```
3. **Opus**:
    - For Ubuntu, you need to install the following packages (not tested):
        ```bash
        sudo apt-get install libopus-dev
        ```
    - For Mac OS X, you need to install the following packages:
        ```bash
        brew install opus
        ```
      Since ctypes find_package is searching for the library in `/usr/local/lib`, 
      you need to copy the opus library to that location:
      ```bash
      sudo mkdir -p /usr/local/lib
      sudo cp $(brew --prefix opus)/lib/libopus.* /usr/local/lib/
      ```
3. **pipenv**:
    ```bash
    pip install pipenv
    ```

### Installation Steps

**Local Development**

1. Clone the repository.

2. Create a virtual environment and install dependencies.
    ```sh
    make install
    ```

**Bundle whole Project**
  ```sh
    make bundle
    ```

## Configuration

The configuration file is located at res/config.json. It includes parameters for the translator, input, and output devices.
Example Configuration

**Example Configuration**
```json
{
  "inputDevice": "default",
  "output": {
    "mumble": {
      "ipAddress": "raspberrypi",
       "port": 64738,
      "languageChannelMapping": {
        "en": "Channel/Subchannel"  // Channel name for the specific translation
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
Extract the bundled zip file into your disired location and
use the following command to run the translation service:
```sh
python main.py 
```

**Command-line Arguments**
- -t, --translator: Translator to use (default: aws)
- -i, --input: Sound input method to use (default: mic)
- -o, --output: Sound output method to use (default: mumble)
- -sl, --source_lang: Source language (default: de)
- -tl, --target_lang: Target language(s) (default: [en])



## Side Notes
Opuslib and pymumble are not maintained anymore.
So, we need to use the forked version of the libraries, 
since some changes were made to the original ones.