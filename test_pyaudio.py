import pyaudio
import wave

CHUNK = 1024
FORMAT = pyaudio.paInt16
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "voice.wav"

p = pyaudio.PyAudio()

default_frames = 1024

#try grabbing the default input device and see if we get lucky
default_input_device = p.get_default_input_device_info()

# verify this is your microphone device 
print(default_input_device)

#if correct then set it as your input device and define some globals
input_device = default_input_device

input_channel_count = input_device["maxInputChannels"]
input_sample_rate = input_device["defaultSampleRate"]
input_dev_index = input_device["index"]

stream = p.open(format=FORMAT,
                channels=input_channel_count,
                rate=int(input_sample_rate),
                input=True,
                input_device_index=input_dev_index,
                frames_per_buffer=CHUNK)

print("* recording")

frames = []

for i in range(0, int(input_sample_rate / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(input_channel_count)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(input_sample_rate)
wf.writeframes(b''.join(frames))
wf.close()