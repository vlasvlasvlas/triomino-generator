"""
Sound Engine for Bot vs Bot Musical Mode.
Generates procedural audio based on tile placements.
"""
import pygame
import numpy as np
import json
import os
from typing import List, Dict, Optional
import math

# Initialize pygame mixer
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)


class SoundEngine:
    """Procedural sound generator for Triomino Bot vs Bot mode."""
    
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Audio state
        self.muted = False
        self.volume = 0.7
        
        # Cache generated sounds
        self._sound_cache: Dict[str, pygame.mixer.Sound] = {}

        # Load Configuration
        self.config = {}
        self.presets = []
        self.events = {}
        self.reload_config()

        # State
        self.current_preset_idx = 0
        self.base_bpm = self.config.get("bpm", 120)
        self.bpm_multiplier = 1.0
    
    def reload_config(self):
        """Load/Reload sound presets and config from JSON."""
        # Try sonic_config.json first, fall back to sound_presets.json
        sonic_path = os.path.join(os.path.dirname(__file__), "sonic_config.json")
        presets_path = os.path.join(os.path.dirname(__file__), "sound_presets.json")
        
        data = {}
        if os.path.exists(sonic_path):
            with open(sonic_path, 'r') as f:
                data = json.load(f)
        elif os.path.exists(presets_path):
            with open(presets_path, 'r') as f:
                data = json.load(f)
        
        self.config = data
        self.presets = data.get("presets", self._default_presets())
        self.events = data.get("events", {})
        
        # Reset cache on reload
        self._sound_cache.clear()
        
    @property
    def tempo_ms(self) -> int:
        """Calculate delay in ms between beats based on BPM."""
        effective_bpm = self.base_bpm * self.bpm_multiplier
        # 60000 ms / BPM = ms per beat
        return int(60000 / max(1, effective_bpm))

    def _default_presets(self) -> List[Dict]:
        """Built-in sound presets."""
        return [
            {
                "name": "Piano",
                "waveform": "sine",
                "base_freq": 261.63,
                "decay": 0.5,
                "scale": [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24, 26]
            }
        ]
    
    @property
    def current_preset(self) -> Dict:
        """Get current sound preset."""
        if not self.presets: return self._default_presets()[0]
        return self.presets[self.current_preset_idx]
    
    @property
    def preset_name(self) -> str:
        """Get current preset name."""
        return self.current_preset.get("name", "Unknown")
    
    def next_preset(self, direction: int = 1):
        """Cycle to next/previous preset."""
        if not self.presets: return
        self.current_preset_idx = (self.current_preset_idx + direction) % len(self.presets)
        self._sound_cache.clear()  # Clear cache on preset change
    
    def adjust_bpm(self, delta: int):
        """Adjust base BPM."""
        self.base_bpm = max(10, min(600, self.base_bpm + delta))

    def adjust_tempo(self, faster: bool = True, step: int = 10) -> int:
        """Compatibility helper for UI callers that expect tempo +/- control."""
        self.adjust_bpm(step if faster else -step)
        return self.base_bpm

    def set_bpm(self, bpm: int):
        """Set specific BPM."""
        self.base_bpm = max(10, min(600, bpm))
    
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
        elif waveform == "noise":
             wave = np.random.uniform(-1, 1, t.shape)
        else:
            wave = np.sin(2 * np.pi * freq * t)  # Default sine
        
        return wave
    
    def _apply_envelope(self, wave: np.ndarray, attack: float, decay: float, release: float) -> np.ndarray:
        """Apply ADSR-like envelope to wave."""
        length = len(wave)
        envelope = np.ones(length)
        sample_rate = 44100
        
        attack_len = int(sample_rate * attack)
        release_len = int(sample_rate * release)
        
        # Ensure lengths fit
        total_env_len = attack_len + release_len
        if total_env_len > length:
             scale = length / total_env_len
             attack_len = int(attack_len * scale)
             release_len = int(release_len * scale)

        # Attack
        if attack_len > 0:
            envelope[:attack_len] = np.linspace(0, 1, attack_len)
        
        # Decay/Sustain part (simplified: just constant 1 for now or exp decay)
        # Using decay param as exponential decay factor for the body
        sustain_len = length - attack_len - release_len
        if sustain_len > 0:
            decay_curve = np.linspace(1, 0.5, sustain_len) ** (1/decay) if decay > 0 else np.ones(sustain_len)
            envelope[attack_len:attack_len+sustain_len] = decay_curve

        # Release
        if release_len > 0:
            start_val = envelope[length-release_len-1] if length-release_len-1 >= 0 else 1.0
            envelope[-release_len:] = np.linspace(start_val, 0, release_len)
            
        return wave * envelope
    
    def _create_sound(self, tile_sum: int) -> pygame.mixer.Sound:
        """Create a sound based on tile value sum."""
        preset = self.current_preset
        
        # Map tile sum (0-15 typical) to scale degree
        scale = preset.get("scale", list(range(16)))
        scale_idx = tile_sum % len(scale)
        semitones = scale[scale_idx]
        
        # Calculate frequency from base + semitones
        base_freq = preset.get("base_freq", 261.63)
        freq = base_freq * (2 ** (semitones / 12))
        
        # Generate waveform
        duration = 0.4 # Fixed buffer length for now
        waveform = preset.get("waveform", "sine")
        wave = self._generate_waveform(freq, duration, waveform)
        
        # Apply envelope
        decay = preset.get("decay", 0.5)
        attack = preset.get("attack", 0.05)
        release = preset.get("release", 0.1)
        
        wave = self._apply_envelope(wave, attack, decay, release)
        
        # Normalize and convert to 16-bit stereo
        wave = (wave * 32767 * self.volume).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo)
    
    def play_event(self, event_name: str, **kwargs):
        """Play a specific game event sound."""
        if self.muted: return
        
        # Check if event is mapped in config
        action = self.events.get(event_name)
        if not action: return 
        
        if event_name == "on_place":
             tile_values = kwargs.get("tile_values", (0,0,0))
             self.play_tile_sound(tile_values)
        elif event_name == "on_draw":
             pass # Placeholder implementation
        elif event_name == "on_pass":
             pass # Placeholder implementation

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
        return f"{mute_str} {self.preset_name} | BPM: {self.base_bpm}"


# Singleton instance
_sound_engine: Optional[SoundEngine] = None

def get_sound_engine() -> SoundEngine:
    """Get or create the sound engine singleton."""
    global _sound_engine
    if _sound_engine is None:
        _sound_engine = SoundEngine()
    return _sound_engine
