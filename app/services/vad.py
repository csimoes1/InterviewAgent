import webrtcvad
import numpy as np
from collections import deque

class VoiceActivityDetector:
    def __init__(self,
                 sample_rate=16000,
                 frame_duration_ms=30,
                 padding_duration_ms=600,  # Increased from 300 to 600
                 aggressiveness=3,
                 speech_end_threshold=0.95):  # New parameter for configurable threshold
        """
        Initialize a VAD detector with configurable pause tolerance.

        Args:
            sample_rate: Audio sample rate in Hz (must be 8000, 16000, 32000 or 48000)
            frame_duration_ms: Duration of each frame in milliseconds (must be 10, 20, or 30)
            padding_duration_ms: Duration of silence padding in milliseconds
            aggressiveness: VAD aggressiveness mode (0-3, 3 being the most aggressive)
            speech_end_threshold: Threshold for determining speech end (0.0-1.0)
                                 Higher values allow longer pauses (default: 0.95)
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.padding_frames = padding_duration_ms // frame_duration_ms
        self.speech_end_threshold = speech_end_threshold

        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad(aggressiveness)

        # Buffer to store frames for silence detection
        self.triggered = False
        self.voiced_frames = []
        self.ring_buffer = deque(maxlen=self.padding_frames)

    def reset(self):
        """Reset VAD state"""
        self.triggered = False
        self.voiced_frames = []
        self.ring_buffer.clear()

    def process_audio(self, audio_data):
        """
        Process audio data and detect voice activity.

        Args:
            audio_data: Audio data as bytes (must be 16-bit PCM)

        Returns:
            (is_speech_ended, speech_frames):
                - is_speech_ended: True if speech has ended
                - speech_frames: Collected speech frames if speech ended, None otherwise
        """
        # Process only the new audio data, don't reprocess
        raw_samples = np.frombuffer(audio_data, dtype=np.int16)
        num_frames = len(raw_samples) // self.frame_size

        speech_ended = False
        result_frames = None

        # Process each frame
        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = raw_samples[start:end]

            # Make sure we have a complete frame
            if len(frame) < self.frame_size:
                continue

            # Convert to bytes for WebRTC VAD
            frame_bytes = frame.tobytes()

            # Check if frame contains speech
            try:
                is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
            except:
                # If we get an error (e.g., wrong frame size), skip this frame
                continue

            if not self.triggered:
                # Not yet triggered
                self.ring_buffer.append((frame, is_speech))
                num_voiced = sum(1 for f, speech in self.ring_buffer if speech)

                # If enough recent frames have contained speech, trigger
                if num_voiced > 0.5 * self.ring_buffer.maxlen:
                    self.triggered = True
                    # Add frames from ring buffer to voiced frames
                    for f, s in self.ring_buffer:
                        self.voiced_frames.append(f)
                    self.ring_buffer.clear()
            else:
                # Already triggered
                self.voiced_frames.append(frame)
                self.ring_buffer.append((frame, is_speech))
                num_unvoiced = sum(1 for f, speech in self.ring_buffer if not speech)

                # Check if speech has ended based on configurable threshold
                # Higher threshold means more non-speech frames are required to end
                if num_unvoiced > self.speech_end_threshold * self.ring_buffer.maxlen:
                    speech_ended = True
                    result_frames = b''.join(f.tobytes() for f in self.voiced_frames)
                    # Reset state after getting speech frames
                    self.reset()
                    # Return immediately to avoid processing more frames after speech end
                    return speech_ended, result_frames

        return speech_ended, result_frames

    def set_pause_tolerance(self, tolerance_ms):
        """
        Set a new pause tolerance duration in milliseconds.

        Args:
            tolerance_ms: Duration in milliseconds for pause tolerance
        """
        # Update padding duration and recalculate padding frames
        self.padding_duration_ms = tolerance_ms
        self.padding_frames = tolerance_ms // self.frame_duration_ms
        # Update ring buffer size
        new_buffer = deque(maxlen=self.padding_frames)
        # Transfer any existing items from old buffer if possible
        for item in self.ring_buffer:
            new_buffer.append(item)
        self.ring_buffer = new_buffer