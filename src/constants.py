INPUT_CHANNELS = 1  # Mono is sufficient for translation and seems to work best
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 16000
CHUNK_LEN = 1024

OUTPUT = ['speaker', 'mumble']

AWS_REGIONS = {
    'us-east-1': 'N. Virginia',
    'us-east-2': 'Ohio',
    'us-west-2': 'Oregon',
    'eu-west-1': 'Ireland',
    'eu-west-2': 'London',
    'eu-central-1': 'Frankfurt',
    'ap-southeast-1': 'Singapore',
    'ap-southeast-2': 'Sydney',
    'ap-northeast-1': 'Tokyo',
    'ca-central-1': 'Canada',
}

AWS_STANDARD_VOICES = {
    'de-DE': {'voice_ids': ['Vicki', 'Marlene', 'Hans']},
    'en-US': {'voice_ids': ['Joanna', 'Salli', 'Matthew', 'Kimberly', 'Kendra', 'Justin', 'Joey', 'Ivy']},
    'en-GB': {'voice_ids': ['Emma', 'Brian', 'Amy']},
    'en-AU': {'voice_ids': ['Russell', 'Nicole']},
    'en-IN': {'voice_ids': ['Raveena', 'Aditi']},
    'en-GB-WLS': {'voice_ids': ['Geraint']},
    'es-US': {'voice_ids': ['Lupe', 'Penélope', 'Miguel']},
    'es-MX': {'voice_ids': ['Mia']},
    'es-ES': {'voice_ids': ['Lucia', 'Enrique', 'Conchita']},
    'fr-FR': {'voice_ids': ['Mathieu', 'Léa', 'Céline']},
    'fr-CA': {'voice_ids': ['Chantal']},
    'it-IT': {'voice_ids': ['Bianca', 'Giorgio', 'Carla']},
    'pt-PT': {'voice_ids': ['Inês', 'Cristiano']},
    'pt-BR': {'voice_ids': ['Vitória', 'Ricardo', 'Camila']},
    'pl-PL': {'voice_ids': ['Maja', 'Jan', 'Jacek', 'Ewa']},
    'nl-NL': {'voice_ids': ['Ruben', 'Lotte']},
    'nb-NO': {'voice_ids': ['Liv']},
    'sv-SE': {'voice_ids': ['Astrid']},
    'da-DK': {'voice_ids': ['Naja', 'Mads']},
    'is-IS': {'voice_ids': ['Karl', 'Dóra']},
    'ru-RU': {'voice_ids': ['Tatyana', 'Maxim']},
    'tr-TR': {'voice_ids': ['Filiz']},
    'ro-RO': {'voice_ids': ['Carmen']},
    'ko-KR': {'voice_ids': ['Seoyeon']},
    'ja-JP': {'voice_ids': ['Takumi', 'Mizuki']},
    'zh-CN': {'voice_ids': ['Zhiyu']},
    'cy-GB': {'voice_ids': ['Gwyneth']},
    'arb': {'voice_ids': ['Zeina']},
}

AWS_NEURAL_VOICES = {
    'ar-AE': {'voice_ids': ['Hala', 'Zayd']},
    'ca-ES': {'voice_ids': ['Arlet']},
    'cs-CZ': {'voice_ids': ['Jitka']},
    'cmn-CN': {'voice_ids': ['Zhiyu']},
    'da-DK': {'voice_ids': ['Sofie']},
    'de-AT': {'voice_ids': ['Hannah']},
    'de-CH': {'voice_ids': ['Sabrina']},
    'de-DE': {'voice_ids': ['Vicki', 'Daniel']},
    'en-AU': {'voice_ids': ['Olivia']},
    'en-GB': {'voice_ids': ['Emma', 'Brian', 'Amy', 'Arthur']},
    'en-IE': {'voice_ids': ['Niamh']},
    'en-IN': {'voice_ids': ['Kajal']},
    'en-NZ': {'voice_ids': ['Aria']},
    'en-SG': {'voice_ids': ['Jasmine']},
    'en-US': {
        'voice_ids': [
            'Danielle',
            'Gregory',
            'Joanna',
            'Ruth',
            'Kevin',
            'Salli',
            'Matthew',
            'Kimberly',
            'Kendra',
            'Justin',
            'Joey',
            'Ivy',
            'Stephen',
        ]
    },
    'en-ZA': {'voice_ids': ['Ayanda']},
    'es-ES': {'voice_ids': ['Lucia', 'Sergio']},
    'es-MX': {'voice_ids': ['Mia', 'Andres']},
    'es-US': {'voice_ids': ['Lupe', 'Pedro']},
    'fi-FI': {'voice_ids': ['Suvi']},
    'fr-BE': {'voice_ids': ['Isabelle']},
    'fr-CA': {'voice_ids': ['Gabrielle', 'Liam']},
    'fr-FR': {'voice_ids': ['Lea', 'Remi']},
    'it-IT': {'voice_ids': ['Bianca', 'Adriano']},
    'ja-JP': {'voice_ids': ['Kazuha', 'Tomoko', 'Takumi']},
    'ko-KR': {'voice_ids': ['Jihye', 'Seoyeon']},
    'nb-NO': {'voice_ids': ['Ida']},
    'nl-BE': {'voice_ids': ['Lisa']},
    'nl-NL': {'voice_ids': ['Laura']},
    'pl-PL': {'voice_ids': ['Ola']},
    'pt-BR': {'voice_ids': ['Vitoria', 'Camila', 'Thiago']},
    'pt-PT': {'voice_ids': ['Ines']},
    'sv-SE': {'voice_ids': ['Elin']},
    'tr-TR': {'voice_ids': ['Burcu']},
    'yue-CN': {'voice_ids': ['Hiujin']},
}

GOOGLE_STANDARD_VOICES = {
    'ar-XA': {'voice_ids': ['ar-XA-Standard-A', 'ar-XA-Standard-B', 'ar-XA-Standard-C', 'ar-XA-Standard-D']},
    'cs-CZ': {'voice_ids': ['cs-CZ-Standard-A']},
    'da-DK': {'voice_ids': ['da-DK-Standard-A', 'da-DK-Standard-C', 'da-DK-Standard-D', 'da-DK-Standard-E']},
    'nl-NL': {'voice_ids': ['nl-NL-Standard-A']},
    'en-AU': {'voice_ids': ['en-AU-Standard-A', 'en-AU-Standard-B', 'en-AU-Standard-C', 'en-AU-Standard-D']},
    'en-IN': {'voice_ids': ['en-IN-Standard-A', 'en-IN-Standard-B', 'en-IN-Standard-C', 'en-IN-Standard-D']},
    'en-GB': {'voice_ids': ['en-GB-Standard-A', 'en-GB-Standard-B', 'en-GB-Standard-C', 'en-GB-Standard-D']},
    'en-US': {
        'voice_ids': [
            'en-US-Standard-A',
            'en-US-Standard-B',
            'en-US-Standard-C',
            'en-US-Standard-D',
            'en-US-Standard-E',
            'en-US-Standard-F',
            'en-US-Standard-G',
            'en-US-Standard-H',
            'en-US-Standard-I',
            'en-US-Standard-J',
        ]
    },
    'fil-PH': {'voice_ids': ['fil-PH-Standard-A']},
    'fi-FI': {'voice_ids': ['fi-FI-Standard-A']},
    'fr-CA': {'voice_ids': ['fr-CA-Standard-A', 'fr-CA-Standard-B', 'fr-CA-Standard-C', 'fr-CA-Standard-D']},
    'fr-FR': {
        'voice_ids': [
            'fr-FR-Standard-A',
            'fr-FR-Standard-B',
            'fr-FR-Standard-C',
            'fr-FR-Standard-D',
            'fr-FR-Standard-E',
        ]
    },
    'de-DE': {'voice_ids': ['de-DE-Standard-A', 'de-DE-Standard-B', 'de-DE-Standard-C', 'de-DE-Standard-D']},
    'el-GR': {'voice_ids': ['el-GR-Standard-A']},
    'hi-IN': {'voice_ids': ['hi-IN-Standard-A', 'hi-IN-Standard-B', 'hi-IN-Standard-C', 'hi-IN-Standard-D']},
    'hu-HU': {'voice_ids': ['hu-HU-Standard-A']},
    'id-ID': {'voice_ids': ['id-ID-Standard-A']},
    'it-IT': {'voice_ids': ['it-IT-Standard-B', 'it-IT-Standard-C']},
    'ja-JP': {'voice_ids': ['ja-JP-Standard-A', 'ja-JP-Standard-B', 'ja-JP-Standard-C', 'ja-JP-Standard-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Standard-A', 'ko-KR-Standard-B', 'ko-KR-Standard-C']},
    'cmn-TW': {'voice_ids': ['cmn-TW-Standard-A']},
    'nb-NO': {'voice_ids': ['nb-NO-Standard-A']},
    'pl-PL': {'voice_ids': ['pl-PL-Standard-A']},
    'pt-BR': {'voice_ids': ['pt-BR-Standard-A']},
    'ru-RU': {'voice_ids': ['ru-RU-Standard-A', 'ru-RU-Standard-B']},
    'sk-SK': {'voice_ids': ['sk-SK-Standard-A']},
    'es-ES': {'voice_ids': ['es-ES-Standard-A']},
    'sv-SE': {'voice_ids': ['sv-SE-Standard-A']},
    'tr-TR': {'voice_ids': ['tr-TR-Standard-A']},
    'uk-UA': {'voice_ids': ['uk-UA-Standard-A']},
    'vi-VN': {'voice_ids': ['vi-VN-Standard-A']},
}

GOOGLE_WAVENET_VOICES = {
    'ar-XA': {'voice_ids': ['ar-XA-Wavenet-A', 'ar-XA-Wavenet-B', 'ar-XA-Wavenet-C', 'ar-XA-Wavenet-D']},
    'cs-CZ': {'voice_ids': ['cs-CZ-Wavenet-A']},
    'da-DK': {'voice_ids': ['da-DK-Wavenet-A', 'da-DK-Wavenet-C', 'da-DK-Wavenet-D', 'da-DK-Wavenet-E']},
    'nl-NL': {'voice_ids': ['nl-NL-Wavenet-A']},
    'en-AU': {'voice_ids': ['en-AU-Wavenet-A', 'en-AU-Wavenet-B', 'en-AU-Wavenet-C', 'en-AU-Wavenet-D']},
    'en-IN': {'voice_ids': ['en-IN-Wavenet-A', 'en-IN-Wavenet-B', 'en-IN-Wavenet-C', 'en-IN-Wavenet-D']},
    'en-GB': {'voice_ids': ['en-GB-Wavenet-A', 'en-GB-Wavenet-B', 'en-GB-Wavenet-C', 'en-GB-Wavenet-D']},
    'en-US': {
        'voice_ids': [
            'en-US-Wavenet-A',
            'en-US-Wavenet-B',
            'en-US-Wavenet-C',
            'en-US-Wavenet-D',
            'en-US-Wavenet-E',
            'en-US-Wavenet-F',
            'en-US-Wavenet-G',
            'en-US-Wavenet-H',
            'en-US-Wavenet-I',
            'en-US-Wavenet-J',
        ]
    },
    'fil-PH': {'voice_ids': ['fil-PH-Wavenet-A']},
    'fi-FI': {'voice_ids': ['fi-FI-Wavenet-A']},
    'fr-CA': {'voice_ids': ['fr-CA-Wavenet-A', 'fr-CA-Wavenet-B', 'fr-CA-Wavenet-C', 'fr-CA-Wavenet-D']},
    'fr-FR': {'voice_ids': ['fr-FR-Wavenet-A', 'fr-FR-Wavenet-B', 'fr-FR-Wavenet-C', 'fr-FR-Wavenet-D']},
    'de-DE': {'voice_ids': ['de-DE-Wavenet-A', 'de-DE-Wavenet-B', 'de-DE-Wavenet-C', 'de-DE-Wavenet-D']},
    'el-GR': {'voice_ids': ['el-GR-Wavenet-A']},
    'hi-IN': {'voice_ids': ['hi-IN-Wavenet-A', 'hi-IN-Wavenet-B', 'hi-IN-Wavenet-C', 'hi-IN-Wavenet-D']},
    'hu-HU': {'voice_ids': ['hu-HU-Wavenet-A']},
    'id-ID': {'voice_ids': ['id-ID-Wavenet-A']},
    'it-IT': {'voice_ids': ['it-IT-Wavenet-B', 'it-IT-Wavenet-C']},
    'ja-JP': {'voice_ids': ['ja-JP-Wavenet-A', 'ja-JP-Wavenet-B', 'ja-JP-Wavenet-C', 'ja-JP-Wavenet-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Wavenet-A', 'ko-KR-Wavenet-B', 'ko-KR-Wavenet-C']},
    'cmn-TW': {'voice_ids': ['cmn-TW-Wavenet-A']},
    'nb-NO': {'voice_ids': ['nb-NO-Wavenet-A']},
    'pl-PL': {'voice_ids': ['pl-PL-Wavenet-A']},
    'pt-BR': {'voice_ids': ['pt-BR-Wavenet-A']},
    'ru-RU': {'voice_ids': ['ru-RU-Wavenet-A', 'ru-RU-Wavenet-B']},
    'sk-SK': {'voice_ids': ['sk-SK-Wavenet-A']},
    'es-ES': {'voice_ids': ['es-ES-Wavenet-A']},
    'sv-SE': {'voice_ids': ['sv-SE-Wavenet-A']},
    'tr-TR': {'voice_ids': ['tr-TR-Wavenet-A']},
    'uk-UA': {'voice_ids': ['uk-UA-Wavenet-A']},
    'vi-VN': {'voice_ids': ['vi-VN-Wavenet-A']},
}

GOOGLE_NEURAL2_VOICES = {
    'ar-XA': {'voice_ids': ['ar-XA-Neural2-A', 'ar-XA-Neural2-B', 'ar-XA-Neural2-C', 'ar-XA-Neural2-D']},
    'bg-BG': {'voice_ids': ['bg-BG-Neural2-A']},
    'ca-ES': {'voice_ids': ['ca-ES-Neural2-A', 'ca-ES-Neural2-B']},
    'he-IL': {'voice_ids': ['he-IL-Neural2-A', 'he-IL-Neural2-B']},
    'ro-RO': {'voice_ids': ['ro-RO-Neural2-A', 'ro-RO-Neural2-B']},
    'sl-SI': {'voice_ids': ['sl-SI-Neural2-A']},
    'sr-RS': {'voice_ids': ['sr-RS-Neural2-A']},
    'th-TH': {'voice_ids': ['th-TH-Neural2-A', 'th-TH-Neural2-B']},
    'sw-KE': {'voice_ids': ['sw-KE-Neural2-A']},
    'cy-GB': {'voice_ids': ['cy-GB-Neural2-A']},
    'cs-CZ': {'voice_ids': ['cs-CZ-Neural2-A']},
    'da-DK': {'voice_ids': ['da-DK-Neural2-A', 'da-DK-Neural2-D', 'da-DK-Neural2-E', 'da-DK-Neural2-F']},
    'nl-NL': {
        'voice_ids': ['nl-NL-Neural2-A', 'nl-NL-Neural2-B', 'nl-NL-Neural2-C', 'nl-NL-Neural2-D', 'nl-NL-Neural2-E']
    },
    'en-AU': {'voice_ids': ['en-AU-Neural2-A', 'en-AU-Neural2-B', 'en-AU-Neural2-C', 'en-AU-Neural2-D']},
    'en-IN': {'voice_ids': ['en-IN-Neural2-A', 'en-IN-Neural2-B', 'en-IN-Neural2-C', 'en-IN-Neural2-D']},
    'en-GB': {
        'voice_ids': ['en-GB-Neural2-A', 'en-GB-Neural2-B', 'en-GB-Neural2-C', 'en-GB-Neural2-D', 'en-GB-Neural2-F']
    },
    'en-US': {
        'voice_ids': [
            'en-US-Neural2-A',
            'en-US-Neural2-C',
            'en-US-Neural2-D',
            'en-US-Neural2-E',
            'en-US-Neural2-F',
            'en-US-Neural2-G',
            'en-US-Neural2-H',
            'en-US-Neural2-I',
            'en-US-Neural2-J',
        ]
    },
    'fil-PH': {'voice_ids': ['fil-PH-Neural2-A', 'fil-PH-Neural2-D']},
    'fi-FI': {'voice_ids': ['fi-FI-Neural2-A']},
    'fr-CA': {'voice_ids': ['fr-CA-Neural2-A', 'fr-CA-Neural2-B', 'fr-CA-Neural2-C', 'fr-CA-Neural2-D']},
    'fr-FR': {
        'voice_ids': ['fr-FR-Neural2-A', 'fr-FR-Neural2-B', 'fr-FR-Neural2-C', 'fr-FR-Neural2-D', 'fr-FR-Neural2-E']
    },
    'de-DE': {
        'voice_ids': ['de-DE-Neural2-A', 'de-DE-Neural2-B', 'de-DE-Neural2-C', 'de-DE-Neural2-D', 'de-DE-Neural2-F']
    },
    'el-GR': {'voice_ids': ['el-GR-Neural2-A']},
    'hi-IN': {'voice_ids': ['hi-IN-Neural2-A', 'hi-IN-Neural2-B', 'hi-IN-Neural2-C', 'hi-IN-Neural2-D']},
    'hu-HU': {'voice_ids': ['hu-HU-Neural2-A']},
    'id-ID': {'voice_ids': ['id-ID-Neural2-A', 'id-ID-Neural2-B', 'id-ID-Neural2-C']},
    'it-IT': {'voice_ids': ['it-IT-Neural2-A', 'it-IT-Neural2-C']},
    'ja-JP': {'voice_ids': ['ja-JP-Neural2-B', 'ja-JP-Neural2-C', 'ja-JP-Neural2-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Neural2-A', 'ko-KR-Neural2-B', 'ko-KR-Neural2-C']},
    'cmn-CN': {'voice_ids': ['cmn-CN-Neural2-A', 'cmn-CN-Neural2-B', 'cmn-CN-Neural2-C', 'cmn-CN-Neural2-D']},
    'nb-NO': {
        'voice_ids': ['nb-NO-Neural2-A', 'nb-NO-Neural2-C', 'nb-NO-Neural2-D', 'nb-NO-Neural2-E', 'nb-NO-Neural2-F']
    },
    'pl-PL': {
        'voice_ids': ['pl-PL-Neural2-A', 'pl-PL-Neural2-B', 'pl-PL-Neural2-C', 'pl-PL-Neural2-D', 'pl-PL-Neural2-E']
    },
    'pt-BR': {'voice_ids': ['pt-BR-Neural2-A', 'pt-BR-Neural2-B', 'pt-BR-Neural2-C']},
    'pt-PT': {'voice_ids': ['pt-PT-Neural2-A', 'pt-PT-Neural2-B', 'pt-PT-Neural2-C', 'pt-PT-Neural2-D']},
    'ru-RU': {
        'voice_ids': ['ru-RU-Neural2-A', 'ru-RU-Neural2-B', 'ru-RU-Neural2-C', 'ru-RU-Neural2-D', 'ru-RU-Neural2-E']
    },
    'sk-SK': {'voice_ids': ['sk-SK-Neural2-A']},
    'es-ES': {
        'voice_ids': [
            'es-ES-Neural2-A',
            'es-ES-Neural2-B',
            'es-ES-Neural2-C',
            'es-ES-Neural2-D',
            'es-ES-Neural2-E',
            'es-ES-Neural2-F',
        ]
    },
    'es-US': {'voice_ids': ['es-US-Neural2-A', 'es-US-Neural2-B', 'es-US-Neural2-C']},
    'sv-SE': {
        'voice_ids': ['sv-SE-Neural2-A', 'sv-SE-Neural2-B', 'sv-SE-Neural2-C', 'sv-SE-Neural2-D', 'sv-SE-Neural2-E']
    },
    'tr-TR': {
        'voice_ids': ['tr-TR-Neural2-A', 'tr-TR-Neural2-B', 'tr-TR-Neural2-C', 'tr-TR-Neural2-D', 'tr-TR-Neural2-E']
    },
    'uk-UA': {'voice_ids': ['uk-UA-Neural2-A']},
    'vi-VN': {'voice_ids': ['vi-VN-Neural2-A', 'vi-VN-Neural2-B', 'vi-VN-Neural2-C', 'vi-VN-Neural2-D']},
}

GOOGLE_STUDIO_VOICES = {
    'de-DE': {'voice_ids': ['de-DE-Studio-B', 'de-DE-Studio-C']},
    'en-GB': {'voice_ids': ['en-GB-Studio-B', 'en-GB-Studio-C']},
    'en-US': {'voice_ids': ['en-US-Studio-M', 'en-US-Studio-O', 'en-US-Studio-Q']},
    'en-IN': {'voice_ids': ['en-IN-Studio-A']},
    'es-ES': {'voice_ids': ['es-ES-Studio-C', 'es-ES-Studio-F']},
    'es-US': {'voice_ids': ['es-US-Studio-B']},
    'fr-CA': {'voice_ids': ['fr-CA-Studio-A']},
    'fr-FR': {'voice_ids': ['fr-FR-Studio-A', 'fr-FR-Studio-D']},
    'it-IT': {'voice_ids': ['it-IT-Studio-A', 'it-IT-Studio-B']},
    'ja-JP': {'voice_ids': ['ja-JP-Studio-B', 'ja-JP-Studio-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Studio-B', 'ko-KR-Studio-C']},
    'pt-BR': {'voice_ids': ['pt-BR-Studio-B', 'pt-BR-Studio-C']},
    'pt-PT': {'voice_ids': ['pt-PT-Studio-A']},
    'ru-RU': {'voice_ids': ['ru-RU-Studio-A']},
}

# Chirp 3 HD voices — same voice names across all supported languages.
# Format: {lang}-Chirp3-HD-{VoiceName}
_CHIRP3_HD_VOICES = [
    'Aoede',
    'Charon',
    'Fenrir',
    'Kore',
    'Leda',
    'Orus',
    'Puck',
    'Schedar',
    'Algieba',
    'Algenib',
    'Alnilam',
    'Despina',
    'Erinome',
    'Gacrux',
    'Iapetus',
    'Laomedeia',
    'Narvi',
    'Pulcherrima',
    'Rasalgethi',
    'Sadachbia',
    'Sadaltager',
    'Sulafat',
    'Umbriel',
    'Vindemiatrix',
    'Wasat',
    'Zubenelgenubi',
]


def _chirp3_hd(lang: str) -> dict:
    return {'voice_ids': [f'{lang}-Chirp3-HD-{v}' for v in _CHIRP3_HD_VOICES]}


GOOGLE_CHIRP3_HD_VOICES = {
    'af-ZA': _chirp3_hd('af-ZA'),
    'am-ET': _chirp3_hd('am-ET'),
    'ar-XA': _chirp3_hd('ar-XA'),
    'az-AZ': _chirp3_hd('az-AZ'),
    'bg-BG': _chirp3_hd('bg-BG'),
    'bn-IN': _chirp3_hd('bn-IN'),
    'ca-ES': _chirp3_hd('ca-ES'),
    'cmn-CN': _chirp3_hd('cmn-CN'),
    'cmn-TW': _chirp3_hd('cmn-TW'),
    'cs-CZ': _chirp3_hd('cs-CZ'),
    'da-DK': _chirp3_hd('da-DK'),
    'de-AT': _chirp3_hd('de-AT'),
    'de-DE': _chirp3_hd('de-DE'),
    'el-GR': _chirp3_hd('el-GR'),
    'en-AU': _chirp3_hd('en-AU'),
    'en-GB': _chirp3_hd('en-GB'),
    'en-IN': _chirp3_hd('en-IN'),
    'en-US': _chirp3_hd('en-US'),
    'es-ES': _chirp3_hd('es-ES'),
    'es-US': _chirp3_hd('es-US'),
    'et-EE': _chirp3_hd('et-EE'),
    'fa-IR': _chirp3_hd('fa-IR'),
    'fi-FI': _chirp3_hd('fi-FI'),
    'fil-PH': _chirp3_hd('fil-PH'),
    'fr-CA': _chirp3_hd('fr-CA'),
    'fr-FR': _chirp3_hd('fr-FR'),
    'gu-IN': _chirp3_hd('gu-IN'),
    'he-IL': _chirp3_hd('he-IL'),
    'hi-IN': _chirp3_hd('hi-IN'),
    'hr-HR': _chirp3_hd('hr-HR'),
    'hu-HU': _chirp3_hd('hu-HU'),
    'id-ID': _chirp3_hd('id-ID'),
    'is-IS': _chirp3_hd('is-IS'),
    'it-IT': _chirp3_hd('it-IT'),
    'ja-JP': _chirp3_hd('ja-JP'),
    'ka-GE': _chirp3_hd('ka-GE'),
    'km-KH': _chirp3_hd('km-KH'),
    'kn-IN': _chirp3_hd('kn-IN'),
    'ko-KR': _chirp3_hd('ko-KR'),
    'lo-LA': _chirp3_hd('lo-LA'),
    'lt-LT': _chirp3_hd('lt-LT'),
    'lv-LV': _chirp3_hd('lv-LV'),
    'ml-IN': _chirp3_hd('ml-IN'),
    'mr-IN': _chirp3_hd('mr-IN'),
    'ms-MY': _chirp3_hd('ms-MY'),
    'ne-NP': _chirp3_hd('ne-NP'),
    'nb-NO': _chirp3_hd('nb-NO'),
    'nl-BE': _chirp3_hd('nl-BE'),
    'nl-NL': _chirp3_hd('nl-NL'),
    'pa-IN': _chirp3_hd('pa-IN'),
    'pl-PL': _chirp3_hd('pl-PL'),
    'pt-BR': _chirp3_hd('pt-BR'),
    'pt-PT': _chirp3_hd('pt-PT'),
    'ro-RO': _chirp3_hd('ro-RO'),
    'ru-RU': _chirp3_hd('ru-RU'),
    'si-LK': _chirp3_hd('si-LK'),
    'sk-SK': _chirp3_hd('sk-SK'),
    'sl-SI': _chirp3_hd('sl-SI'),
    'sr-RS': _chirp3_hd('sr-RS'),
    'sv-SE': _chirp3_hd('sv-SE'),
    'sw-KE': _chirp3_hd('sw-KE'),
    'ta-IN': _chirp3_hd('ta-IN'),
    'te-IN': _chirp3_hd('te-IN'),
    'th-TH': _chirp3_hd('th-TH'),
    'tr-TR': _chirp3_hd('tr-TR'),
    'uk-UA': _chirp3_hd('uk-UA'),
    'ur-IN': _chirp3_hd('ur-IN'),
    'vi-VN': _chirp3_hd('vi-VN'),
    'uz-UZ': _chirp3_hd('uz-UZ'),
    'cy-GB': _chirp3_hd('cy-GB'),
}

TRANSLATOR = {
    'aws': {
        'standard': AWS_STANDARD_VOICES,
        'neural': AWS_NEURAL_VOICES,
    },
    'google': {
        'standard': GOOGLE_STANDARD_VOICES,
        'wavenet': GOOGLE_WAVENET_VOICES,
        'neural2': GOOGLE_NEURAL2_VOICES,
        'studio': GOOGLE_STUDIO_VOICES,
        'chirp3-hd': GOOGLE_CHIRP3_HD_VOICES,
    },
}

GOOGLE_REGIONS = {
    'europe-west3': 'Frankfurt',
    'europe-west2': 'London',
    'us-central1': 'Iowa',
    'us-east1': 'S. Carolina',
    'us-east4': 'N. Virginia',
    'us-west1': 'Oregon',
    'asia-southeast1': 'Singapore',
    'asia-northeast1': 'Tokyo',
}

GOOGLE_ENDPOINTING_OPTIONS = {
    'Normal': 'standard',
    'Fast': 'short',
    'Max': 'supershort',
}

# Windows Audio Host APIs
HOST_API_NAMES = {
    0: 'MME',  # (Windows Multimedia Extension
    1: 'DirectSound',
    2: 'WASAPI',  # (Windows Audio Session API)
    3: 'ASIO',  # (Audio Stream Input/Output)
}
