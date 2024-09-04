import pyaudio

def list_devices():
    p = pyaudio.PyAudio()
    
    # Get input devices
    print("Input Devices:")
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            print(f"{device_info['index']}. {device_info['name']}")

    # Get output devices
    print("\nOutput Devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info.get('maxOutputChannels') > 0:
            print(f"{device_info['index']}. {device_info['name']}")

if __name__ == "__main__":
    list_devices()