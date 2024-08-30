import json
import argparse
import logging
import os
from translation import Translation
from translators.aws_translator import AWSTranslator
from sound_inputs.microphone import Microphone
from sound_outputs.mumble import MumbleClient
from sound_outputs.speaker import Speaker

CONFIG_PATH = 'res/config.json'

LOGGER = logging.getLogger()
LOGGER.setLevel(os.getenv('LOG_LEVEL') or logging.INFO)


def main():
    """Main function to run the translation service script."""
    parser = argparse.ArgumentParser(description='Translation service script.')
    parser.add_argument('-t', '--translator', default='aws', help='Translator to use (default: aws)')
    parser.add_argument('-i', '--input', default='mic', help='Sound input method to use (default: mic)')
    parser.add_argument('-o', '--output', default='mumble', choices=['mumble', 'speaker'], help='Sound output method to use (default: mumble)')
    parser.add_argument('-sl', '--source_lang', default='de', choices=['de', 'en'], help='Source language (default: de)')
    parser.add_argument('-tl', '--target_lang', nargs='+', default=['en'], choices=['en', 'de', 'ru', 'pl', 'ro'], help='Target language(s) multiple selections soon possible (default: [en])')

    args = parser.parse_args()
    config = load_config(CONFIG_PATH)

    if args.translator == 'aws':
        Translator = AWSTranslator(config)
    else:
        raise ValueError(f"Unsupported translator: {args.translator}")

    if args.input == 'mic':
        sound_input = Microphone(config)
    else:
        raise ValueError(f"Unsupported input method: {args.input}")

    if args.output == 'mumble':
        sound_output = MumbleClient(config, args.target_lang[0])
        sound_output.connect()
    elif args.output == 'speaker':
        sound_output = Speaker(config)
    else:
        raise ValueError(f"Unsupported output method: {args.output}")

    translation = Translation(
        config,
        Translator,
        sound_input,
        sound_output,
        args.source_lang,
        args.target_lang[0]  # Assuming only one target language for simplicity
    )

    try:
        translation.run()
    finally:
        LOGGER.info('Translation stopped')
        if args.output == 'mumble':
            sound_output.disconnect()


def load_config(path: str) -> dict:
    """Loads the configuration from a JSON file.

    Args:
        path (str): The path to the configuration file.

    Returns:
        Dict: The loaded configuration dictionary.
    """
    with open(path, 'r') as file:
        return json.load(file)


if __name__ == '__main__':
    main()