#!/usr/bin/env python3
"""
Create a simple test audio file for WebSocket testing
"""

import wave
import numpy as np

def create_test_audio(filename="test-meeting.wav", duration=5):
    """Create a simple test audio file with some tone"""
    
    sample_rate = 16000
    samples = int(sample_rate * duration)
    
    # Generate a simple tone (440 Hz sine wave)
    t = np.linspace(0, duration, samples, False)
    audio_data = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz tone at 30% volume
    
    # Add some variation to make it more realistic
    audio_data += np.sin(2 * np.pi * 880 * t) * 0.1  # Add harmonic
    audio_data += np.random.normal(0, 0.05, samples)  # Add some noise
    
    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"✅ Created test audio file: {filename}")
    print(f"   Duration: {duration}s, Sample rate: {sample_rate}Hz, Samples: {samples}")

if __name__ == "__main__":
    create_test_audio()