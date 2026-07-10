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
    'af-ZA': {'voice_ids': ['af-ZA-Standard-A']},
    'ar-XA': {'voice_ids': ['ar-XA-Standard-A', 'ar-XA-Standard-B', 'ar-XA-Standard-C', 'ar-XA-Standard-D']},
    'bg-BG': {'voice_ids': ['bg-BG-Standard-B']},
    'bn-IN': {'voice_ids': ['bn-IN-Standard-A', 'bn-IN-Standard-B', 'bn-IN-Standard-C', 'bn-IN-Standard-D']},
    'ca-ES': {'voice_ids': ['ca-ES-Standard-B']},
    'cmn-TW': {'voice_ids': ['cmn-TW-Standard-A', 'cmn-TW-Standard-B', 'cmn-TW-Standard-C']},
    'cs-CZ': {'voice_ids': ['cs-CZ-Standard-B']},
    'cmn-CN': {'voice_ids': ['cmn-CN-Standard-A', 'cmn-CN-Standard-B', 'cmn-CN-Standard-C', 'cmn-CN-Standard-D']},
    'da-DK': {'voice_ids': ['da-DK-Standard-F', 'da-DK-Standard-G']},
    'de-DE': {'voice_ids': ['de-DE-Standard-G', 'de-DE-Standard-H']},
    'en-AU': {'voice_ids': ['en-AU-Standard-A', 'en-AU-Standard-B', 'en-AU-Standard-C', 'en-AU-Standard-D']},
    'el-GR': {'voice_ids': ['el-GR-Standard-B']},
    'es-ES': {'voice_ids': ['es-ES-Standard-E', 'es-ES-Standard-F', 'es-ES-Standard-G', 'es-ES-Standard-H']},
    'en-IN': {
        'voice_ids': [
            'en-IN-Standard-A',
            'en-IN-Standard-B',
            'en-IN-Standard-C',
            'en-IN-Standard-D',
            'en-IN-Standard-E',
            'en-IN-Standard-F'
        ]},
    'en-GB': {
        'voice_ids': [
            'en-GB-Standard-A',
            'en-GB-Standard-B',
            'en-GB-Standard-C',
            'en-GB-Standard-D',
            'en-GB-Standard-F',
            'en-GB-Standard-N',
            'en-GB-Standard-O'
        ]},
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
    'eu-ES': {'voice_ids': ['eu-ES-Standard-B']},
    'es-US': {'voice_ids': ['es-US-Standard-A', 'es-US-Standard-B', 'es-US-Standard-C']},
    'et-EE': {'voice_ids': ['et-EE-Standard-A']},
    'fil-PH': {'voice_ids': ['fil-PH-Standard-A', 'fil-PH-Standard-B', 'fil-PH-Standard-C', 'fil-PH-Standard-D']},
    'fi-FI': {'voice_ids': ['fi-FI-Standard-B']},
    'fr-CA': {'voice_ids': ['fr-CA-Standard-A', 'fr-CA-Standard-B', 'fr-CA-Standard-C', 'fr-CA-Standard-D']},
    'fr-FR': {'voice_ids': ['fr-FR-Standard-F', 'fr-FR-Standard-G']},
    'gl-ES': {'voice_ids': ['gl-ES-Standard-B']},
    'gu-IN': {'voice_ids': ['gu-IN-Standard-A', 'gu-IN-Standard-B', 'gu-IN-Standard-C', 'gu-IN-Standard-D']},
    'he-IL': {'voice_ids': ['he-IL-Standard-A', 'he-IL-Standard-B', 'he-IL-Standard-C', 'he-IL-Standard-D']},
    'hi-IN': {
        'voice_ids': [
            'hi-IN-Standard-A',
            'hi-IN-Standard-B',
            'hi-IN-Standard-C',
            'hi-IN-Standard-D',
            'hi-IN-Standard-E',
            'hi-IN-Standard-F'
        ]},
    'hu-HU': {'voice_ids': ['hu-HU-Standard-B']},
    'id-ID': {'voice_ids': ['id-ID-Standard-A', 'id-ID-Standard-B', 'id-ID-Standard-C', 'id-ID-Standard-D']},
    'it-IT': {'voice_ids': ['it-IT-Standard-E', 'it-IT-Standard-F']},
    'is-IS': {'voice_ids': ['is-IS-Standard-B']},
    'ja-JP': {'voice_ids': ['ja-JP-Standard-A', 'ja-JP-Standard-B', 'ja-JP-Standard-C', 'ja-JP-Standard-D']},
    'kn-IN': {'voice_ids': ['kn-IN-Standard-A', 'kn-IN-Standard-B', 'kn-IN-Standard-C', 'kn-IN-Standard-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Standard-A', 'ko-KR-Standard-B', 'ko-KR-Standard-C', 'ko-KR-Standard-D']},
    'lv-LV': {'voice_ids': ['lv-LV-Standard-B']},
    'lt-LT': {'voice_ids': ['lt-LT-Standard-B']},
    'ms-MY': {'voice_ids': ['ms-MY-Standard-A', 'ms-MY-Standard-B', 'ms-MY-Standard-C', 'ms-MY-Standard-D']},
    'ml-IN': {'voice_ids': ['ml-IN-Standard-A', 'ml-IN-Standard-B', 'ml-IN-Standard-C', 'ml-IN-Standard-D']},
    'mr-IN': {'voice_ids': ['mr-IN-Standard-A', 'mr-IN-Standard-B', 'mr-IN-Standard-C']},
    'nl-BE': {'voice_ids': ['nl-NL-Standard-C', 'nl-NL-Standard-D']},
    'nl-NL': {'voice_ids': ['nl-NL-Standard-F', 'nl-NL-Standard-G']},
    'nb-NO': {'voice_ids': ['nb-NO-Standard-F', 'nb-NO-Standard-G']},
    'pa-IN': {'voice_ids': ['pa-IN-Standard-A', 'pa-IN-Standard-B', 'pa-IN-Standard-C', 'pa-IN-Standard-D']},
    'pl-PL': {'voice_ids': ['pl-PL-Standard-F', 'pl-PL-Standard-G']},
    'pt-BR': {
        'voice_ids': [
            'pt-BR-Standard-A',
            'pt-BR-Standard-B',
            'pt-BR-Standard-C',
            'pt-BR-Standard-D',
            'pt-BR-Standard-E'
        ]},
    'pt-PT': {'voice_ids': ['pt-PT-Standard-E', 'pt-PT-Standard-F']},
    'ru-RU': {
        'voice_ids': [
            'ru-RU-Standard-A',
            'ru-RU-Standard-B',
            'ru-RU-Standard-C',
            'ru-RU-Standard-D',
            'ru-RU-Standard-E'
        ]},
    'sk-SK': {'voice_ids': ['sk-SK-Standard-B']},
    'sr-RS': {'voice_ids': ['sr-RS-Standard-B']},
    'sv-SE': {
        'voice_ids': [
            'sv-SE-Standard-A',
            'sv-SE-Standard-B',
            'sv-SE-Standard-C',
            'sv-SE-Standard-D',
            'sv-SE-Standard-E',
            'sv-SE-Standard-F',
            'sv-SE-Standard-G'
        ]},
    'ta-IN': {'voice_ids': ['ta-IN-Standard-A', 'ta-IN-Standard-B', 'ta-IN-Standard-C', 'ta-IN-Standard-D']},
    'te-IN': {'voice_ids': ['te-IN-Standard-A', 'te-IN-Standard-B', 'te-IN-Standard-C', 'te-IN-Standard-D']},
    'th-TH': {'voice_ids': ['th-TH-Standard-A']},
    'tr-TR': {
        'voice_ids': [
            'tr-TR-Standard-A',
            'tr-TR-Standard-B',
            'tr-TR-Standard-C',
            'tr-TR-Standard-D',
            'tr-TR-Standard-E'
        ]},
    'uk-UA': {'voice_ids': ['uk-UA-Standard-B']},
    'ur-IN': {'voice_ids': ['ur-IN-Standard-A', 'ur-IN-Standard-B']},
    'vi-VN': {'voice_ids': ['vi-VN-Standard-A', 'vi-VN-Standard-B', 'vi-VN-Standard-C', 'vi-VN-Standard-D']},
    'yue-HK': {'voice_ids': ['yue-HK-Standard-A', 'yue-HK-Standard-B', 'yue-HK-Standard-C', 'yue-HK-Standard-D']},
}

GOOGLE_WAVENET_VOICES = {
    'ar-XA': {'voice_ids': ['ar-XA-Wavenet-A', 'ar-XA-Wavenet-B', 'ar-XA-Wavenet-C', 'ar-XA-Wavenet-D']},
    'bn-IN': {'voice_ids': ['bn-IN-Wavenet-A', 'bn-IN-Wavenet-B', 'bn-IN-Wavenet-C', 'bn-IN-Wavenet-D']},
    'cs-CZ': {'voice_ids': ['cs-CZ-Wavenet-B']},
    'cmn-CN': {'voice_ids': ['cmn-CN-Wavenet-A', 'cmn-CN-Wavenet-B', 'cmn-CN-Wavenet-C', 'cmn-CN-Wavenet-D']},
    'cmn-TW': {'voice_ids': ['cmn-TW-Wavenet-A', 'cmn-TW-Wavenet-B', 'cmn-TW-Wavenet-C']},
    'da-DK': {'voice_ids': ['da-DK-Wavenet-F', 'da-DK-Wavenet-G']},
    'de-DE': {'voice_ids': ['de-DE-Wavenet-G', 'de-DE-Wavenet-H']},
    'en-AU': {'voice_ids': ['en-AU-Wavenet-A', 'en-AU-Wavenet-B', 'en-AU-Wavenet-C', 'en-AU-Wavenet-D']},
    'en-IN': {
        'voice_ids': [
            'en-IN-Wavenet-A',
            'en-IN-Wavenet-B',
            'en-IN-Wavenet-C',
            'en-IN-Wavenet-D',
            'en-IN-Wavenet-E',
            'en-IN-Wavenet-F',
        ]
    },
    'en-GB': {
        'voice_ids': [
            'en-GB-Wavenet-A',
            'en-GB-Wavenet-B',
            'en-GB-Wavenet-C',
            'en-GB-Wavenet-D',
            'en-GB-Wavenet-F',
            'en-GB-Wavenet-N',
            'en-GB-Wavenet-O',
        ]
    },
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
    'es-US': {'voice_ids': ['es-US-Wavenet-A', 'es-US-Wavenet-B', 'es-US-Wavenet-C']},
    'es-ES': {'voice_ids': ['es-ES-Wavenet-E', 'es-ES-Wavenet-F', 'es-ES-Wavenet-G', 'es-ES-Wavenet-H']},
    'el-GR': {'voice_ids': ['el-GR-Wavenet-B']},
    'fil-PH': {'voice_ids': ['fil-PH-Wavenet-A', 'fil-PH-Wavenet-B', 'fil-PH-Wavenet-C', 'fil-PH-Wavenet-D']},
    'fi-FI': {'voice_ids': ['fi-FI-Wavenet-B']},
    'fr-CA': {'voice_ids': ['fr-CA-Wavenet-A', 'fr-CA-Wavenet-B', 'fr-CA-Wavenet-C', 'fr-CA-Wavenet-D']},
    'fr-FR': {'voice_ids': ['fr-FR-Wavenet-F', 'fr-FR-Wavenet-G']},
    'gu-IN': {'voice_ids': ['gu-IN-Wavenet-A', 'gu-IN-Wavenet-B', 'gu-IN-Wavenet-C', 'gu-IN-Wavenet-D']},
    'he-IL': {'voice_ids': ['he-IL-Wavenet-A', 'he-IL-Wavenet-B', 'he-IL-Wavenet-C', 'he-IL-Wavenet-D']},
    'hi-IN': {
        'voice_ids': [
            'hi-IN-Wavenet-A',
            'hi-IN-Wavenet-B',
            'hi-IN-Wavenet-C',
            'hi-IN-Wavenet-D',
            'hi-IN-Wavenet-E',
            'hi-IN-Wavenet-F',
        ]
    },
    'hu-HU': {'voice_ids': ['hu-HU-Wavenet-B']},
    'id-ID': {'voice_ids': ['id-ID-Wavenet-A', 'id-ID-Wavenet-B', 'id-ID-Wavenet-C', 'id-ID-Wavenet-D']},
    'it-IT': {'voice_ids': ['it-IT-Wavenet-E', 'it-IT-Wavenet-F']},
    'ja-JP': {'voice_ids': ['ja-JP-Wavenet-A', 'ja-JP-Wavenet-B', 'ja-JP-Wavenet-C', 'ja-JP-Wavenet-D']},
    'kn-IN': {'voice_ids': ['kn-IN-Wavenet-A', 'kn-IN-Wavenet-B', 'kn-IN-Wavenet-C', 'kn-IN-Wavenet-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Wavenet-A', 'ko-KR-Wavenet-B', 'ko-KR-Wavenet-C', 'ko-KR-Wavenet-D']},
    'ml-IN': {'voice_ids': ['ml-IN-Wavenet-A', 'ml-IN-Wavenet-B', 'ml-IN-Wavenet-C', 'ml-IN-Wavenet-D']},
    'mr-IN': {'voice_ids': ['mr-IN-Wavenet-A', 'mr-IN-Wavenet-B', 'mr-IN-Wavenet-C']},
    'ms-MY': {'voice_ids': ['ms-MY_Wavenet-A', 'ms-MY_Wavenet-B', 'ms-MY_Wavenet-C', 'ms-MY_Wavenet-D']},
    'nl-BE': {'voice_ids': ['nl-BE-Wavenet-C', 'nl-BE-Wavenet-D']},
    'nl-NL': {'voice_ids': ['nl-NL-Wavenet-F', 'nl-NL-Wavenet-G']},
    'nb-NO': {'voice_ids': ['nb-NO-Wavenet-F', 'nb-NO-Wavenet-G']},
    'pa-IN': {'voice_ids': ['pa-IN-Wavenet-A', 'pa-IN-Wavenet-B', 'pa-IN-Wavenet-C', 'pa-IN-Wavenet-D']},
    'pl-PL': {'voice_ids': ['pl-PL-Wavenet-F', 'pl-PL-Wavenet-G']},
    'pt-BR': {
        'voice_ids': ['pt-BR-Wavenet-A', 'pt-BR-Wavenet-B', 'pt-BR-Wavenet-C', 'pt-BR-Wavenet-D', 'pt-BR-Wavenet-E']
    },
    'pt-PT': {'voice_ids': ['pt-PT-Wavenet-E', 'pt-PT-Wavenet-F']},
    'ro-RO': {'voice_ids': ['ro-RO-Wavenet-B']},
    'ru-RU': {
        'voice_ids': ['ru-RU-Wavenet-A', 'ru-RU-Wavenet-B', 'ru-RU-Wavenet-C', 'ru-RU-Wavenet-D', 'ru-RU-Wavenet-E']
    },
    'sk-SK': {'voice_ids': ['sk-SK-Wavenet-B']},
    'sv-SE': {
        'voice_ids': [
            'sv-SE-Wavenet-A',
            'sv-SE-Wavenet-B',
            'sv-SE-Wavenet-C',
            'sv-SE-Wavenet-D',
            'sv-SE-Wavenet-E',
            'sv-SE-Wavenet-F',
            'sv-SE-Wavenet-G',
        ]
    },
    'ta-IN': {'voice_ids': ['ta-IN-Wavenet-A', 'ta-IN-Wavenet-B', 'ta-IN-Wavenet-C', 'ta-IN-Wavenet-D']},
    'tr-TR': {
        'voice_ids': ['tr-TR-Wavenet-A', 'tr-TR-Wavenet-B', 'tr-TR-Wavenet-C', 'tr-TR-Wavenet-D', 'tr-TR-Wavenet-E']
    },
    'uk-UA': {'voice_ids': ['uk-UA-Wavenet-B']},
    'ur-IN': {'voice_ids': ['ur-IN-Wavenet-A', 'ur-IN-Wavenet-B']},
    'vi-VN': {'voice_ids': ['vi-VN-Wavenet-A', 'vi-VN-Wavenet-B', 'vi-VN-Wavenet-C', 'vi-VN-Wavenet-D']},
}

GOOGLE_NEURAL2_VOICES = {
    'da-DK': {'voice_ids': ['da-DK-Neural2-F']},
    'en-AU': {'voice_ids': ['en-AU-Neural2-A', 'en-AU-Neural2-B', 'en-AU-Neural2-C', 'en-AU-Neural2-D']},
    'en-IN': {'voice_ids': ['en-IN-Neural2-A', 'en-IN-Neural2-B', 'en-IN-Neural2-C', 'en-IN-Neural2-D']},
    'en-GB': {
        'voice_ids': [
            'en-GB-Neural2-A',
            'en-GB-Neural2-B',
            'en-GB-Neural2-C',
            'en-GB-Neural2-D',
            'en-GB-Neural2-F',
            'en-GB-Neural2-N',
            'en-GB-Neural2-O'
        ]},
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
    'fr-CA': {'voice_ids': ['fr-CA-Neural2-A', 'fr-CA-Neural2-B', 'fr-CA-Neural2-C', 'fr-CA-Neural2-D']},
    'fr-FR': {'voice_ids': ['fr-FR-Neural2-F', 'fr-FR-Neural2-G']},
    'de-DE': {'voice_ids': ['de-DE-Neural2-G', 'de-DE-Neural2-H']},
    'hi-IN': {'voice_ids': ['hi-IN-Neural2-A', 'hi-IN-Neural2-B', 'hi-IN-Neural2-C', 'hi-IN-Neural2-D']},
    'it-IT': {'voice_ids': ['it-IT-Neural2-A', 'it-IT-Neural2-E', 'it-IT-Neural2-F']},
    'ja-JP': {'voice_ids': ['ja-JP-Neural2-B', 'ja-JP-Neural2-C', 'ja-JP-Neural2-D']},
    'ko-KR': {'voice_ids': ['ko-KR-Neural2-A', 'ko-KR-Neural2-B', 'ko-KR-Neural2-C']},
    'pt-BR': {'voice_ids': ['pt-BR-Neural2-A', 'pt-BR-Neural2-B', 'pt-BR-Neural2-C']},
    'es-ES': {
        'voice_ids': [
            'es-ES-Neural2-A',
            'es-ES-Neural2-E',
            'es-ES-Neural2-F',
            'es-ES-Neural2-G',
            'es-ES-Neural2-H',
        ]
    },
    'es-US': {'voice_ids': ['es-US-Neural2-A', 'es-US-Neural2-B', 'es-US-Neural2-C']},
    'vi-VN': {'voice_ids': ['vi-VN-Neural2-A', 'vi-VN-Neural2-D']},
}

GOOGLE_STUDIO_VOICES = {
    'de-DE': {'voice_ids': ['de-DE-Studio-B', 'de-DE-Studio-C']},
    'en-GB': {'voice_ids': ['en-GB-Studio-B', 'en-GB-Studio-C']},
    'en-US': {'voice_ids': ['en-US-Studio-O', 'en-US-Studio-Q']},
    'es-ES': {'voice_ids': ['es-ES-Studio-C', 'es-ES-Studio-F']},
    'es-US': {'voice_ids': ['es-US-Studio-B']},
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
    'ar-XA': _chirp3_hd('ar-XA'),
    'bg-BG': _chirp3_hd('bg-BG'),
    'bn-IN': _chirp3_hd('bn-IN'),
    'cmn-CN': _chirp3_hd('cmn-CN'),
    'cs-CZ': _chirp3_hd('cs-CZ'),
    'da-DK': _chirp3_hd('da-DK'),
    'de-DE': _chirp3_hd('de-DE'),
    'el-GR': _chirp3_hd('el-GR'),
    'en-AU': _chirp3_hd('en-AU'),
    'en-GB': _chirp3_hd('en-GB'),
    'en-IN': _chirp3_hd('en-IN'),
    'en-US': _chirp3_hd('en-US'),
    'es-ES': _chirp3_hd('es-ES'),
    'es-US': _chirp3_hd('es-US'),
    'et-EE': _chirp3_hd('et-EE'),
    'fi-FI': _chirp3_hd('fi-FI'),
    'fr-CA': _chirp3_hd('fr-CA'),
    'fr-FR': _chirp3_hd('fr-FR'),
    'gu-IN': _chirp3_hd('gu-IN'),
    'he-IL': _chirp3_hd('he-IL'),
    'hi-IN': _chirp3_hd('hi-IN'),
    'hr-HR': _chirp3_hd('hr-HR'),
    'hu-HU': _chirp3_hd('hu-HU'),
    'id-ID': _chirp3_hd('id-ID'),
    'it-IT': _chirp3_hd('it-IT'),
    'ja-JP': _chirp3_hd('ja-JP'),
    'kn-IN': _chirp3_hd('kn-IN'),
    'ko-KR': _chirp3_hd('ko-KR'),
    'lt-LT': _chirp3_hd('lt-LT'),
    'lv-LV': _chirp3_hd('lv-LV'),
    'ml-IN': _chirp3_hd('ml-IN'),
    'mr-IN': _chirp3_hd('mr-IN'),
    'nb-NO': _chirp3_hd('nb-NO'),
    'nl-BE': _chirp3_hd('nl-BE'),
    'nl-NL': _chirp3_hd('nl-NL'),
    'pa-IN': _chirp3_hd('pa-IN'),
    'pl-PL': _chirp3_hd('pl-PL'),
    'pt-BR': _chirp3_hd('pt-BR'),
    'ro-RO': _chirp3_hd('ro-RO'),
    'ru-RU': _chirp3_hd('ru-RU'),
    'sk-SK': _chirp3_hd('sk-SK'),
    'sl-SI': _chirp3_hd('sl-SI'),
    'sr-RS': _chirp3_hd('sr-RS'),
    'sv-SE': _chirp3_hd('sv-SE'),
    'ta-IN': _chirp3_hd('ta-IN'),
    'te-IN': _chirp3_hd('te-IN'),
    'th-TH': _chirp3_hd('th-TH'),
    'tr-TR': _chirp3_hd('tr-TR'),
    'uk-UA': _chirp3_hd('uk-UA'),
    'ur-IN': _chirp3_hd('ur-IN'),
    'vi-VN': _chirp3_hd('vi-VN'),
    'yue-HK': _chirp3_hd('yue-HK'),
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

# Reduced set of "global" STT regions. Each region is paired with the STT model that
# offers the widest language support for that region/endpoint. The model is therefore
# implicitly derived from the selected region (see GoogleSettings) and not user-selectable.
GOOGLE_STT_REGIONS = {
    'us': 'chirp_3',
    'eu': 'chirp_3',
    'europe-west4': 'chirp_2',
    'us-central1': 'chirp_2',
    'asia-southeast1': 'chirp_2',
}

# Streaming-capable Speech-to-Text v2 models suitable for live translation.
# Batch-only / high-latency models (e.g. latest_long) are intentionally excluded.
#
# Supported languages per model must be verified against the official docs, since
# Google updates/extends this list regularly:
# https://cloud.google.com/speech-to-text/v2/docs/speech-to-text-supported-languages
GOOGLE_STT_MODELS = {
    'chirp_3': [
        'af-ZA', 'sq-AL', 'am-ET', 'ar-DZ', 'ar-BH', 'ar-EG', 'ar-IQ', 'ar-IL',
        'ar-JO', 'ar-KW', 'ar-LB', 'ar-MR', 'ar-MA', 'ar-OM', 'ar-XA', 'ar-QA',
        'ar-SA', 'ar-PS', 'ar-SY', 'ar-TN', 'ar-AE', 'ar-YE', 'hy-AM', 'as-IN',
        'ast-ES', 'az-AZ', 'eu-ES', 'bn-BD', 'bn-IN', 'bg-BG', 'my-MM', 'ca-ES',
        'cmn-Hans-CN', 'yue-Hant-HK', 'cmn-Hant-TW', 'hr-HR', 'cs-CZ', 'da-DK',
        'nl-NL', 'en-AU', 'en-IN', 'en-PH', 'en-GB', 'en-US', 'et-EE', 'fil-PH',
        'fi-FI', 'fr-CA', 'fr-FR', 'gl-ES', 'ka-GE', 'de-DE', 'el-GR', 'gu-IN',
        'ha-NG', 'iw-IL', 'hi-IN', 'hu-HU', 'is-IS', 'id-ID', 'it-IT', 'ja-JP',
        'jv-ID', 'kn-IN', 'kk-KZ', 'km-KH', 'ko-KR', 'ky-KG', 'lo-LA', 'lv-LV',
        'lt-LT', 'lb-LU', 'mk-MK', 'ms-MY', 'ml-IN', 'mt-MT', 'mi-NZ', 'mr-IN',
        'mn-MN', 'ne-NP', 'no', 'or-IN', 'fa-IR', 'pl-PL', 'pt-BR', 'pt-PT',
        'pa-Guru-IN', 'ro-RO', 'ru-RU', 'nso-ZA', 'sr-RS', 'sk-SK', 'sl-SI',
        'es-MX', 'es-ES', 'es-US', 'sw', 'sw-KE', 'sv-SE', 'ta-IN', 'te-IN',
        'th-TH', 'tr-TR', 'uk-UA', 'ur-PK', 'uz-UZ', 'vi-VN', 'cy-GB','wo-SN',
        'xh-ZA', 'yo-NG', 'zu-ZA',
    ],
    'chirp_2': [
        'af-ZA', 'sq-AL', 'am-ET', 'ar-EG', 'hy-AM', 'rup-BG', 'as-IN', 'ast-ES',
        'az-AZ', 'eu-ES', 'be-BY', 'bn-BD', 'bn-IN', 'bs-BA', 'bg-BG', 'my-MM',
        'ca-ES', 'ceb-PH', 'ckb-IQ', 'cmn-Hans-CN', 'yue-Hant-HK', 'cmn-Hant-TW', 'hr-HR', 'cs-CZ',
        'da-DK', 'nl-NL', 'en-AU', 'en-IN', 'en-GB', 'en-US', 'et-EE', 'fil-PH',
        'fi-FI', 'fr-CA', 'fr-FR', 'ff-SN', 'gl-ES', 'lg-UG', 'ka-GE', 'de-DE',
        'el-GR', 'gu-IN', 'ha-NG', 'iw-IL', 'hi-IN', 'hu-HU', 'is-IS', 'ig-NG',
        'id-ID', 'ga-IE', 'it-IT', 'ja-JP', 'jv-ID', 'kea-CV', 'kam-KE', 'kn-IN',
        'kk-KZ', 'km-KH', 'ko-KR', 'ky-KG', 'lo-LA', 'lv-LV', 'ln-CD', 'lt-LT',
        'luo-KE', 'lb-LU', 'mk-MK', 'ms-MY', 'ml-IN', 'mt-MT', 'mi-NZ', 'mr-IN',
        'mn-MN', 'ne-NP', 'no', 'ny-MW', 'oc-FR', 'or-IN', 'om-ET', 'ps-AF',
        'fa-IR', 'pl-PL', 'pt-BR', 'pt-PT', 'pa-Guru-IN', 'ro-RO', 'ru-RU', 'nso-ZA',
        'sr-RS', 'sn-ZW', 'sd-IN', 'si-LK', 'sk-SK', 'sl-SI', 'so-SO', 'es-419',
        'es-ES', 'es-US', 'su-ID', 'sw', 'sw-KE', 'sv-SE', 'tg-TJ', 'ta-IN',
        'te-IN', 'th-TH', 'tr-TR', 'uk-UA', 'umb-AO', 'ur-PK', 'uz-UZ', 'vi-VN',
        'cy-GB', 'wo-SN', 'xh-ZA', 'yo-NG', 'zu-ZA'
    ]
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
