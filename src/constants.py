INPUT_CHANNELS = 1  # Mono is sufficient for translation and seems to work best
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 16000
CHUNK_LEN = 1024

OUTPUT = ['speaker', 'mumble']

AWS_REGIONS = {
    'us-east-1': 'N. Virginia',
    'us-east-2': 'Ohio',
    'us-west-1': 'N. California',
    'us-west-2': 'Oregon',
    'eu-west-1': 'Ireland',
    'eu-west-2': 'London',
    'eu-west-3': 'Paris',
    'eu-central-1': 'Frankfurt',
    'eu-north-1': 'Stockholm',
    'ap-southeast-1': 'Singapore',
    'ap-southeast-2': 'Sydney',
    'ap-northeast-1': 'Tokyo',
    'ap-northeast-2': 'Seoul',
    'ca-central-1': 'Canada',
    'sa-east-1': 'São Paulo',
}

TRANSLATOR = {
    'aws': {
        'ar-AE': {'voice_ids': ['Zeina']},
        'bg-BG': {'voice_ids': ['Daria']},
        'cmn-CN': {'voice_ids': ['Zhiyu']},
        'cs-CZ': {'voice_ids': ['Iveta']},
        'cy-GB': {'voice_ids': ['Gwyneth']},
        'da-DK': {'voice_ids': ['Naja', 'Mads']},
        'de-DE': {'voice_ids': ['Marlene', 'Hans']},
        'el-GR': {'voice_ids': ['Nikos']},
        'en-AU': {'voice_ids': ['Nicole', 'Russell']},
        'en-GB': {'voice_ids': ['Amy', 'Brian', 'Emma']},
        'en-GB-WLS': {'voice_ids': ['Geraint']},
        'en-IN': {'voice_ids': ['Aditi', 'Raveena']},
        'en-US': {'voice_ids': ['Joanna', 'Joey', 'Justin', 'Kendra', 'Kimberly', 'Salli', 'Ivy', 'Matthew']},
        'en-ZA': {'voice_ids': ['Ayanda']},
        'es-ES': {'voice_ids': ['Conchita', 'Enrique', 'Lucia']},
        'es-MX': {'voice_ids': ['Mia']},
        'es-US': {'voice_ids': ['Lupe', 'Penelope', 'Miguel']},
        'fi-FI': {'voice_ids': ['Suvi']},
        'fr-CA': {'voice_ids': ['Chantal']},
        'fr-FR': {'voice_ids': ['Celine', 'Mathieu']},
        'he-IL': {'voice_ids': ['Carmit']},
        'hi-IN': {'voice_ids': ['Aditi']},
        'hu-HU': {'voice_ids': ['Dora']},
        'id-ID': {'voice_ids': ['Gadis']},
        'is-IS': {'voice_ids': ['Karl', 'Dora']},
        'it-IT': {'voice_ids': ['Carla', 'Giorgio']},
        'ja-JP': {'voice_ids': ['Mizuki', 'Takumi']},
        'ko-KR': {'voice_ids': ['Seoyeon']},
        'ms-MY': {'voice_ids': ['Ivy']},
        'nb-NO': {'voice_ids': ['Liv']},
        'nl-NL': {'voice_ids': ['Lotte', 'Ruben']},
        'pl-PL': {'voice_ids': ['Ewa', 'Jacek', 'Jan', 'Maja']},
        'pt-BR': {'voice_ids': ['Ricardo', 'Vitoria']},
        'pt-PT': {'voice_ids': ['Ines', 'Cristiano']},
        'ro-RO': {'voice_ids': ['Carmen']},
        'ru-RU': {'voice_ids': ['Tatyana', 'Maxim']},
        'sv-SE': {'voice_ids': ['Astrid']},
        'tr-TR': {'voice_ids': ['Filiz']},
        'vi-VN': {'voice_ids': ['Linh']},
        'th-TH': {'voice_ids': ['Narin']},
        'ta-IN': {'voice_ids': ['Valli']},
    }
}

# Windows Audio Host APIs
HOST_API_NAMES = {
    0: 'MME',  # (Windows Multimedia Extension
    1: 'DirectSound',
    2: 'WASAPI',  # (Windows Audio Session API)
    3: 'ASIO',  # (Audio Stream Input/Output)
}
