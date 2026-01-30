"""
Sound Engine for Bot vs Bot Musical Mode.
Generates procedural audio based on tile placements.
"""
import pygame
import numpy as np
import json
import os
from typing import List, Dict, Optional

# Initialize pygame mixer
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)


class SoundEngine:
    """Procedural sound generator for Triomino Bot vs Bot mode."""
    
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Tempo control (ms between AI moves)
        self.tempo_ms = 800
        self.min_tempo = 100
        self.max_tempo = 2000
        self.tempo_step = 100
        
        # Sound preset system
        self.presets = self._load_presets()
        self.current_preset_idx = 0
        
        # Audio state
        self.muted = False
        self.volume = 0.7
        
        # Cache generated sounds
        self._sound_cache: Dict[str, pygame.mixer.Sound] = {}
    
    def _load_presets(self) -> List[Dict]:
        """Load sound presets from JSON or use defaults."""
        presets_path = os.path.join(os.path.dirname(__file__), "sound_presets.json")
        
        if os.path.exists(presets_path):
            with open(presets_path, 'r') as f:
                data = json.load(f)
                return data.get("presets", self._default_presets())
        
        return self._default_presets()
    
    def _default_presets(self) -> List[Dict]:
        """Built-in sound presets."""
        return [
            {
                "name": "Piano",
                "waveform": "sine",
                "base_freq": 261.63,  # C4
                "decay": 0.5,
                "scale": [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24, 26]  # Major scale intervals
            },
            {
                "name": "8-Bit",
                "waveform": "square",
                "base_freq": 220.0,  # A3
                "decay": 0.3,
                "scale": [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24, 27, 29, 31, 34, 36]  # Minor pentatonic
            },
            {
                "name": "Moog Bass",
                "waveform": "sawtooth",
                "base_freq": 110.0,  # A2
                "decay": 0.4,
                "scale": [0, 2, 3, 5, 7, 8, 10, 12, 14, 15, 17, 19, 20, 22, 24, 26]  # Natural minor
            },
            {
                "name": "Synth Pad",
                "waveform": "triangle",
                "base_freq": 329.63,  # E4
                "decay": 0.8,
                "scale": [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24, 26, 28, 31, 33, 36]  # Pentatonic major
            },
            {
                "name": "Bells",
                "waveform": "sine",
                "base_freq": 523.25,  # C5
                "decay": 1.0,
                "scale": [0, 4, 7, 12, 16, 19, 24, 28, 31, 36, 40, 43, 48, 52, 55, 60]  # Overtone series
            }
        ]
    
    @property
    def current_preset(self) -> Dict:
        """Get current sound preset."""
        return self.presets[self.current_preset_idx]
    
    @property
    def preset_name(self) -> str:
        """Get current preset name."""
        return self.current_preset.get("name", "Unknown")
    
    def next_preset(self, direction: int = 1):
        """Cycle to next/previous preset."""
        self.current_preset_idx = (self.current_preset_idx + direction) % len(self.presets)
        self._sound_cache.clear()  # Clear cache on preset change
    
    def adjust_tempo(self, faster: bool):
        """Adjust tempo (AI move speed)."""
        if faster:
            self.tempo_ms = max(self.min_tempo, self.tempo_ms - self.tempo_step)
        else:
            self.tempo_ms = min(self.max_tempo, self.tempo_ms + self.tempo_step)
    
    def toggle_mute(self):
        """Toggle audio mute."""
        self.muted = not self.muted
    
    def _generate_waveform(self, freq: float, duration: float, waveform: str) -> np.ndarray:
        """Generate a waveform array."""
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        if waveform == "sine":
            wave = np.sin(2 * np.pi * freq * t)
        elif waveform == "square":
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif waveform == "sawtooth":
            wave = 2 * (t * freq - np.floor(0.5 + t * freq))
        elif waveform == "triangle":
            wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        else:
            wave = np.sin(2 * np.pi * freq * t)  # Default sine
        
        return wave
    
    def _apply_envelope(self, wave: np.ndarray, decay: float) -> np.ndarray:
        """Apply ADSR-like envelope to wave."""
        length = len(wave)
        envelope = np.ones(length)
        
        # Attack (5% of duration)
        attack_len = int(length * 0.05)
        envelope[:attack_len] = np.linspace(0, 1, attack_len)
        
        # Decay/Sustain/Release
        decay_start = int(length * 0.1)
        envelope[decay_start:] = np.linspace(1, 0, length - decay_start) ** (1 / decay)
        
        return wave * envelope
    
    def _create_sound(self, tile_sum: int) -> pygame.mixer.Sound:
        """Create a sound based on tile value sum."""
        preset = self.current_preset
        
        # Map tile sum (0-15) to scale degree
        scale = preset.get("scale", list(range(16)))
        semitones = scale[min(tile_sum, len(scale) - 1)]
        
        # Calculate frequency from base + semitones
        base_freq = preset.get("base_freq", 261.63)
        freq = base_freq * (2 ** (semitones / 12))
        
        # Generate waveform
        duration = 0.4
        waveform = preset.get("waveform", "sine")
        wave = self._generate_waveform(freq, duration, waveform)
        
        # Apply envelope
        decay = preset.get("decay", 0.5)
        wave = self._apply_envelope(wave, decay)
        
        # Normalize and convert to 16-bit stereo
        wave = (wave * 32767 * self.volume).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    
    def play_tile_sound(self, tile_values: tuple):
        """Play sound for a placed tile based on its values."""
        if self.muted:
            return
        
        tile_sum = sum(tile_values)
        cache_key = f"{self.current_preset_idx}_{tile_sum}"
        
        if cache_key not in self._sound_cache:
            self._sound_cache[cache_key] = self._create_sound(tile_sum)
        
        self._sound_cache[cache_key].play()
    
    def get_status_text(self) -> str:
        """Get formatted status string for HUD."""
        mute_str = "🔇" if self.muted else "🔊"
        return f"{mute_str} {self.preset_name} | Tempo: {self.tempo_ms}ms"


# Singleton instance
_sound_engine: Optional[SoundEngine] = None

def get_sound_engine() -> SoundEngine:
    """Get or create the sound engine singleton."""
    global _sound_engine
    if _sound_engine is None:
        _sound_engine = SoundEngine()
    return _sound_engine
