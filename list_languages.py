import boto3


region = 'eu-central-1'
polly = boto3.client('polly', region_name = region)
translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)


print('Polly Voices')
for voice in polly.describe_voices().get('Voices'):
    print(voice)

print('Translate Languages')
for language in translate.list_languages().get('Languages'):
    print(language)