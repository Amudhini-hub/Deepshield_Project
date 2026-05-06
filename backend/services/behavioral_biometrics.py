"""
Behavioral Biometrics Service
Analyzes user typing patterns, mouse movements, and interaction patterns
"""

from typing import Dict, List
import logging
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BehavioralProfile:
    """User's behavioral profile"""
    user_id: str
    typing_speed: float
    typing_rhythm: float
    error_rate: float
    mouse_velocity: float
    mouse_acceleration: float
    click_interval: float
    interaction_pattern: Dict
    created_at: datetime
    confidence: float


@dataclass
class BehavioralAnalysis:
    """Result of behavioral analysis"""
    is_legitimate: bool
    confidence: float
    typing_score: float
    mouse_score: float
    interaction_score: float
    anomaly_flags: List[str]
    risk_level: str


class BehavioralBiometricsEngine:
    """Analyzes behavioral biometrics for authentication"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.typing_threshold = self.config.get('typing_threshold', 0.8)
        self.mouse_threshold = self.config.get('mouse_threshold', 0.75)
        self.interaction_threshold = self.config.get('interaction_threshold', 0.8)
        self.profiles: Dict[str, BehavioralProfile] = {}
    
    def create_baseline(self, user_id: str, events: List[Dict]) -> BehavioralProfile:
        """Create baseline behavioral profile from multiple events"""
        
        # Extract typing patterns
        typing_data = self._extract_typing_patterns(events)
        typing_speed = typing_data.get('speed', 50)
        typing_rhythm = typing_data.get('rhythm', 0.7)
        error_rate = typing_data.get('error_rate', 0.05)
        
        # Extract mouse patterns
        mouse_data = self._extract_mouse_patterns(events)
        mouse_velocity = mouse_data.get('velocity', 300)
        mouse_acceleration = mouse_data.get('acceleration', 100)
        
        # Extract interaction patterns
        click_interval = self._calculate_click_interval(events)
        
        interaction_pattern = {
            'average_session_duration': self._calculate_session_duration(events),
            'active_time_percentage': self._calculate_active_time(events),
            'click_frequency': self._calculate_click_frequency(events),
            'scroll_frequency': self._calculate_scroll_frequency(events),
            'keyboard_frequency': self._calculate_keyboard_frequency(events)
        }
        
        profile = BehavioralProfile(
            user_id=user_id,
            typing_speed=typing_speed,
            typing_rhythm=typing_rhythm,
            error_rate=error_rate,
            mouse_velocity=mouse_velocity,
            mouse_acceleration=mouse_acceleration,
            click_interval=click_interval,
            interaction_pattern=interaction_pattern,
            created_at=datetime.now(),
            confidence=0.8
        )
        
        self.profiles[user_id] = profile
        return profile
    
    def analyze_user_behavior(self, user_id: str, events: List[Dict]) -> BehavioralAnalysis:
        """
        Analyze current user behavior against baseline
        
        Args:
            user_id: User identifier
            events: List of user interaction events
            
        Returns:
            BehavioralAnalysis result
        """
        
        if user_id not in self.profiles:
            return BehavioralAnalysis(
                is_legitimate=True,
                confidence=0.0,
                typing_score=0.5,
                mouse_score=0.5,
                interaction_score=0.5,
                anomaly_flags=["No baseline profile"],
                risk_level="LOW"
            )
        
        baseline = self.profiles[user_id]
        
        # Analyze typing patterns
        typing_score = self._score_typing_patterns(events, baseline)
        
        # Analyze mouse patterns
        mouse_score = self._score_mouse_patterns(events, baseline)
        
        # Analyze interaction patterns
        interaction_score = self._score_interaction_patterns(events, baseline)
        
        # Combine scores
        combined_score = (typing_score + mouse_score + interaction_score) / 3.0
        is_legitimate = combined_score >= 0.7
        
        # Identify anomalies
        anomalies = []
        if typing_score < 0.6:
            anomalies.append("Typing pattern anomaly")
        if mouse_score < 0.6:
            anomalies.append("Mouse movement anomaly")
        if interaction_score < 0.6:
            anomalies.append("Interaction pattern anomaly")
        
        # Determine risk level
        risk_level = self._determine_risk_level(combined_score)
        
        return BehavioralAnalysis(
            is_legitimate=is_legitimate,
            confidence=combined_score,
            typing_score=typing_score,
            mouse_score=mouse_score,
            interaction_score=interaction_score,
            anomaly_flags=anomalies,
            risk_level=risk_level
        )
    
    def _extract_typing_patterns(self, events: List[Dict]) -> Dict:
        """Extract typing speed and rhythm from events"""
        keyboard_events = [e for e in events if e.get('type') == 'keypress']
        
        if len(keyboard_events) < 2:
            return {'speed': 50, 'rhythm': 0.7, 'error_rate': 0.05}
        
        # Calculate inter-keystroke time
        times = [e.get('timestamp', 0) for e in keyboard_events]
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        
        avg_interval = np.mean(intervals) if intervals else 100
        rhythm = np.std(intervals) / avg_interval if intervals and avg_interval > 0 else 0.5
        
        # Speed in words per minute (rough estimate)
        total_time = times[-1] - times[0] if times else 1
        num_words = len(keyboard_events) / 5.0
        wpm = (num_words / total_time) * 60 if total_time > 0 else 50
        
        # Error rate estimation
        error_events = [e for e in keyboard_events if e.get('is_error', False)]
        error_rate = len(error_events) / len(keyboard_events) if keyboard_events else 0
        
        return {
            'speed': wpm,
            'rhythm': min(rhythm, 1.0),
            'error_rate': error_rate
        }
    
    def _extract_mouse_patterns(self, events: List[Dict]) -> Dict:
        """Extract mouse velocity and acceleration"""
        mouse_events = [e for e in events if e.get('type') == 'mousemove']
        
        if len(mouse_events) < 2:
            return {'velocity': 300, 'acceleration': 100}
        
        # Calculate velocities
        velocities = []
        for i in range(1, len(mouse_events)):
            prev = mouse_events[i-1]
            curr = mouse_events[i]
            
            dx = curr.get('x', 0) - prev.get('x', 0)
            dy = curr.get('y', 0) - prev.get('y', 0)
            dt = curr.get('timestamp', 0) - prev.get('timestamp', 0)
            
            if dt > 0:
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(velocity)
        
        avg_velocity = np.mean(velocities) if velocities else 300
        acceleration = np.std(velocities) if velocities else 100
        
        return {
            'velocity': avg_velocity,
            'acceleration': acceleration
        }
    
    def _score_typing_patterns(self, current_events: List[Dict], baseline: BehavioralProfile) -> float:
        """Score current typing pattern against baseline"""
        current_patterns = self._extract_typing_patterns(current_events)
        
        # Compare typing speed
        speed_ratio = current_patterns.get('speed', 50) / (baseline.typing_speed + 1)
        speed_score = max(0, 1 - abs(speed_ratio - 1))
        
        # Compare rhythm consistency
        rhythm_score = 1 - abs(current_patterns.get('rhythm', 0.5) - baseline.typing_rhythm)
        
        # Compare error rate
        error_ratio = current_patterns.get('error_rate', 0) / (baseline.error_rate + 0.01)
        error_score = max(0, 1 - min(error_ratio, 2))
        
        return (speed_score + rhythm_score + error_score) / 3.0
    
    def _score_mouse_patterns(self, current_events: List[Dict], baseline: BehavioralProfile) -> float:
        """Score current mouse pattern against baseline"""
        current_patterns = self._extract_mouse_patterns(current_events)
        
        # Compare mouse velocity
        vel_ratio = current_patterns.get('velocity', 300) / (baseline.mouse_velocity + 1)
        vel_score = max(0, 1 - abs(vel_ratio - 1) * 0.5)
        
        # Compare acceleration
        accel_ratio = current_patterns.get('acceleration', 100) / (baseline.mouse_acceleration + 1)
        accel_score = max(0, 1 - abs(accel_ratio - 1) * 0.3)
        
        return (vel_score + accel_score) / 2.0
    
    def _score_interaction_patterns(self, current_events: List[Dict], baseline: BehavioralProfile) -> float:
        """Score current interaction patterns against baseline"""
        current_pattern = {
            'average_session_duration': self._calculate_session_duration(current_events),
            'active_time_percentage': self._calculate_active_time(current_events),
            'click_frequency': self._calculate_click_frequency(current_events),
            'scroll_frequency': self._calculate_scroll_frequency(current_events),
            'keyboard_frequency': self._calculate_keyboard_frequency(current_events)
        }
        
        baseline_pattern = baseline.interaction_pattern
        
        # Calculate similarity
        similarity_scores = []
        for key in current_pattern:
            if baseline_pattern.get(key, 0) > 0:
                ratio = current_pattern[key] / (baseline_pattern[key] + 0.001)
                similarity = max(0, 1 - abs(ratio - 1) * 0.5)
                similarity_scores.append(similarity)
        
        return np.mean(similarity_scores) if similarity_scores else 0.5
    
    def _calculate_session_duration(self, events: List[Dict]) -> float:
        """Calculate average session duration"""
        if not events:
            return 0
        times = [e.get('timestamp', 0) for e in events]
        return (max(times) - min(times)) if times else 0
    
    def _calculate_active_time(self, events: List[Dict]) -> float:
        """Calculate percentage of active time"""
        if not events:
            return 0
        active_events = [e for e in events if e.get('is_active', False)]
        return len(active_events) / len(events) if events else 0
    
    def _calculate_click_frequency(self, events: List[Dict]) -> float:
        """Calculate click frequency"""
        click_events = [e for e in events if e.get('type') == 'click']
        duration = self._calculate_session_duration(events)
        return len(click_events) / (duration + 1)
    
    def _calculate_scroll_frequency(self, events: List[Dict]) -> float:
        """Calculate scroll frequency"""
        scroll_events = [e for e in events if e.get('type') == 'scroll']
        duration = self._calculate_session_duration(events)
        return len(scroll_events) / (duration + 1)
    
    def _calculate_keyboard_frequency(self, events: List[Dict]) -> float:
        """Calculate keyboard activity frequency"""
        keyboard_events = [e for e in events if e.get('type') == 'keypress']
        duration = self._calculate_session_duration(events)
        return len(keyboard_events) / (duration + 1)
    
    def _calculate_click_interval(self, events: List[Dict]) -> float:
        """Calculate average interval between clicks"""
        click_events = [e for e in events if e.get('type') == 'click']
        if len(click_events) < 2:
            return 0
        
        times = [e.get('timestamp', 0) for e in click_events]
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        return np.mean(intervals) if intervals else 0
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score >= 0.8:
            return "LOW"
        elif score >= 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
