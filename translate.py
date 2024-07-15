import boto3
import asyncio
import pyaudio
import concurrent
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import wave


recorded_frames = []
FORMAT = pyaudio.paInt16
WAVE_OUTPUT_FILENAME = "voice.wav"
region = 'eu-central-1'
polly = boto3.client('polly', region_name = region)
translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
pa = pyaudio.PyAudio()



#params for AWS Services
params = {}

# source language
# from german
params['source_language'] = "de"
params['lang_code_for_transcribe'] = "de-DE"

# target language
# to english
# params['target_language'] = "en"
# params['lang_code_for_polly'] = "en-US"
# params['voice_id'] = "Kendra"

# # to polish
# params['target_language'] = "pl"
# params['lang_code_for_polly'] = "pl-PL"
# params['voice_id'] = "Jacek"

# to russian
params['target_language'] = "ru"
params['lang_code_for_polly'] = "ru-RU"
params['voice_id'] = "Maxim"

#try grabbing the default input device and see if we get lucky
default_input_device = pa.get_default_input_device_info()

# verify this is your microphone device 
print(default_input_device)

#if correct then set it as your input device and define some globals
input_device = default_input_device

input_channel_count = input_device["maxInputChannels"]
input_sample_rate = input_device["defaultSampleRate"]
input_dev_index = input_device["index"]


default_frames = int(input_sample_rate/2)


async def mic_stream():
    # This function wraps the raw input stream from the microphone forwarding
    # the blocks to an asyncio.Queue.
    
    loop = asyncio.get_event_loop()
    input_queue = asyncio.Queue()
    
    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(input_queue.put_nowait, indata)
        return (indata, pyaudio.paContinue)
        
    # Be sure to use the correct parameters for the audio stream that matches
    # the audio formats described for the source language you'll be using:
    # https://docs.aws.amazon.com/transcribe/latest/dg/streaming.html
    
    print(input_device)
    
    #Open stream
    stream = pa.open(format = FORMAT,
                channels = input_channel_count,
                rate = int(input_sample_rate),
                input = True,
                frames_per_buffer = default_frames,
                input_device_index = input_dev_index,
                stream_callback=callback)
    # Initiate the audio stream and asynchronously yield the audio chunks
    # as they become available.
    stream.start_stream()
    print("started stream")
    while True:
        indata = await input_queue.get()
        yield indata

#text will come from MyEventsHandler
def aws_polly_tts(text):

    response = polly.synthesize_speech(
        Engine = 'standard',
        LanguageCode = params['lang_code_for_polly'],
        Text=text,
        VoiceId = params['voice_id'],
        OutputFormat = "pcm",
    )
    output_bytes = response['AudioStream']
    
    #play to the speakers
    write_to_speaker_stream(output_bytes)
    
#how to write audio bytes to speakers

def write_to_speaker_stream(output_bytes):
    """Consumes bytes in chunks to produce the response's output'"""
    print("Streaming started...")
    chunk_len = 1024
    channels = 1
    sample_rate = 16000
    
    if output_bytes:
        polly_stream = pa.open(
                    format = pyaudio.paInt16,
                    channels = channels,
                    rate = sample_rate,
                    output = True,
                    )
        #this is a blocking call - will sort this out with concurrent later
        while True:
            data = output_bytes.read(chunk_len)
            polly_stream.write(data)
            
        #If there's no more data to read, stop streaming
            if not data:
                output_bytes.close()
                polly_stream.stop_stream()
                polly_stream.close()
                break
        print("Streaming completed.")
    else:
        print("Nothing to stream.")


#use concurrent package to create an executor object with 3 workers ie threads
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):

        #If the transcription is finalized, send it to translate

        results = transcript_event.transcript.results
        if len(results) > 0:
            if len(results[0].alternatives) > 0:
                transcript = results[0].alternatives[0].transcript
                print("transcript:", transcript)

                if hasattr(results[0], "is_partial") and results[0].is_partial == False:
                    
                    #translate only 1 channel. the other channel is a duplicate
                    if results[0].channel_id == "ch_0":
                        trans_result = translate.translate_text(
                            Text = transcript,
                            SourceLanguageCode = params['source_language'],
                            TargetLanguageCode = params['target_language']
                        )
                        print("translated text:" + trans_result.get("TranslatedText"))
                        text = trans_result.get("TranslatedText")

                        #we run aws_polly_tts with a non-blocking executor at every loop iteration
                        await loop.run_in_executor(executor, aws_polly_tts, text)

async def loop_me():
# Setup up our client with our chosen AWS region

    client = TranscribeStreamingClient(region=region)
    stream = await client.start_stream_transcription(
        language_code=params['lang_code_for_transcribe'],
        media_sample_rate_hz=int(input_sample_rate),
        media_encoding="pcm",
    )
    async def write_chunks(stream):
        
        # This connects the raw audio chunks generator coming from the microphone
        # and passes them along to the transcription stream.
        print("getting mic stream")
        async for chunk in mic_stream():
            recorded_frames.append(chunk)
            await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()

    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(stream), handler.handle_events())

#write a proper while loop here
loop = asyncio.get_event_loop()
try:
    while True:
        loop.run_until_complete(loop_me())
except KeyboardInterrupt:
    print('loop stopped')
loop.close()