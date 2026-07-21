from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class InputSettings:
    input_device: Optional[str]
    input_device_index: Optional[int]
    input_sample_rate: int
    input_channels: int


@dataclass
class SpeakerSettings:
    output_device: Optional[str]
    output_device_index: Optional[int]


@dataclass
class MumbleSettings:
    ip_address: str
    port: int
    language_channel_mapping: Dict[str, str]
    use_custom_server: bool = False
    superuser_password: Optional[str] = None


@dataclass
class OutputSettings:
    output_method: Optional[str]
    output_sample_rate: int
    chunk_len: int
    speaker_settings: SpeakerSettings
    mumble_settings: MumbleSettings


@dataclass
class LanguageSettings:
    voice_id: str
    show_transcript: bool
    engine: str = 'standard'


@dataclass
class AWSSettings:
    region: str
    source_language: str
    show_source_transcript: bool
    target_languages: Dict[str, LanguageSettings]


@dataclass
class GoogleSettings:
    credentials_path: str
    source_language: str
    show_source_transcript: bool
    target_languages: Dict[str, LanguageSettings]
    endpointing_sensitivity: str = 'short'
    region: str = 'eu'


@dataclass
class TranslatorSettings:
    translator: str
    aws_settings: Optional[AWSSettings] = field(default=None)
    google_settings: Optional[GoogleSettings] = field(default=None)


@dataclass
class UserConfig:
    input_settings: InputSettings
    output_settings: OutputSettings
    translator_settings: TranslatorSettings
    theme: str = 'light'
