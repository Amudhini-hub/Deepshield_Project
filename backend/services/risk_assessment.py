"""
Risk Assessment Engine
Evaluates overall authentication risk based on multiple factors
"""

from typing import Dict, List
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RiskFactors:
    """Risk factors for assessment"""
    biometric_score: float
    behavioral_score: float
    device_score: float
    location_score: float
    time_score: float
    network_score: float
    attempt_history_score: float


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_score: float
    risk_level: str
    confidence: float
    factors: Dict
    additional_verification_needed: bool
    recommended_action: str
    timestamp: datetime


class RiskAssessmentEngine:
    """Main risk assessment engine"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.risk_threshold = self.config.get('risk_threshold', 70)
        self.adaptive_threshold = True
        
    def assess_authentication_risk(
        self,
        user_id: str,
        biometric_analysis: Dict,
        behavioral_analysis: Dict,
        device_context: Dict,
        location_context: Dict,
        attempt_history: Dict
    ) -> RiskAssessment:
        """
        Comprehensive risk assessment
        
        Args:
            user_id: User identifier
            biometric_analysis: Biometric analysis results
            behavioral_analysis: Behavioral analysis results
            device_context: Device information
            location_context: Location information
            attempt_history: User's authentication history
            
        Returns:
            RiskAssessment with risk score and actions
        """
        
        # Extract scores from analyses
        factors = RiskFactors(
            biometric_score=biometric_analysis.get('overall_score', 0.5),
            behavioral_score=behavioral_analysis.get('confidence', 0.5),
            device_score=self._assess_device_risk(device_context),
            location_score=self._assess_location_risk(location_context, user_id),
            time_score=self._assess_time_risk(attempt_history),
            network_score=self._assess_network_risk(device_context),
            attempt_history_score=self._assess_attempt_history_risk(attempt_history)
        )
        
        # Calculate weighted risk score
        risk_score = self._calculate_risk_score(factors)
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Determine if additional verification is needed
        additional_verification = risk_score > self.risk_threshold
        
        # Recommended action
        recommended_action = self._get_recommended_action(risk_level, factors)
        
        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=self._calculate_confidence(factors),
            factors={
                'biometric': factors.biometric_score,
                'behavioral': factors.behavioral_score,
                'device': factors.device_score,
                'location': factors.location_score,
                'time': factors.time_score,
                'network': factors.network_score,
                'attempt_history': factors.attempt_history_score
            },
            additional_verification_needed=additional_verification,
            recommended_action=recommended_action,
            timestamp=datetime.now()
        )
    
    def _assess_device_risk(self, device_context: Dict) -> float:
        """Assess risk based on device properties"""
        risk = 0.0
        
        # Check if device is recognized
        if not device_context.get('is_registered', False):
            risk += 0.3
        
        # Check device compromises
        if device_context.get('has_malware', False):
            risk += 0.4
        
        # Check if device is rooted/jailbroken
        if device_context.get('is_rooted', False):
            risk += 0.25
        
        # Check for VPN/proxy
        if device_context.get('uses_vpn', False):
            risk += 0.15
        
        # Normalize to 0-1
        return min(risk, 1.0)
    
    def _assess_location_risk(self, location_context: Dict, user_id: str) -> float:
        """Assess risk based on location"""
        risk = 0.0
        
        current_location = location_context.get('current', {})
        last_location = location_context.get('last', {})
        
        # Check if location is unusual
        if not current_location.get('is_known', False):
            risk += 0.2
        
        # Calculate distance traveled
        if last_location:
            distance = self._calculate_distance(
                current_location.get('latitude', 0),
                current_location.get('longitude', 0),
                last_location.get('latitude', 0),
                last_location.get('longitude', 0)
            )
            
            time_diff = location_context.get('time_diff_minutes', 60)
            
            # Calculate impossible travel speed
            if time_diff > 0:
                speed = distance / (time_diff / 60)  # km/h
                if speed > 900:  # Faster than airplane
                    risk += 0.4
                elif speed > 200:  # Unusual speed
                    risk += 0.2
        
        # Check for blacklisted locations
        if current_location.get('is_blacklisted', False):
            risk += 0.3
        
        # Normalize to 0-1
        return min(risk, 1.0)
    
    def _assess_time_risk(self, attempt_history: Dict) -> float:
        """Assess risk based on time patterns"""
        risk = 0.0
        
        # Check if login time is unusual
        if attempt_history.get('is_unusual_time', False):
            risk += 0.15
        
        # Check for multiple failed attempts
        failed_attempts = attempt_history.get('failed_attempts_today', 0)
        if failed_attempts >= 3:
            risk += min(0.3, failed_attempts * 0.1)
        
        # Check for rapid attempts
        if attempt_history.get('rapid_attempts', False):
            risk += 0.25
        
        # Normalize to 0-1
        return min(risk, 1.0)
    
    def _assess_network_risk(self, device_context: Dict) -> float:
        """Assess risk based on network properties"""
        risk = 0.0
        
        # Check for open/public WiFi
        if device_context.get('network_type') == 'public_wifi':
            risk += 0.2
        
        # Check for untrusted network
        if not device_context.get('is_trusted_network', True):
            risk += 0.15
        
        # Check for suspicious ASN
        if device_context.get('is_suspicious_asn', False):
            risk += 0.2
        
        # Normalize to 0-1
        return min(risk, 1.0)
    
    def _assess_attempt_history_risk(self, attempt_history: Dict) -> float:
        """Assess risk based on authentication history"""
        risk = 0.0
        
        # Check account age
        account_age_days = attempt_history.get('account_age_days', 365)
        if account_age_days < 30:
            risk += 0.2
        
        # Check for suspicious patterns
        if attempt_history.get('account_compromised_history', False):
            risk += 0.3
        
        # Check for multiple failed MFA attempts
        failed_mfa = attempt_history.get('failed_mfa_attempts', 0)
        if failed_mfa >= 2:
            risk += min(0.25, failed_mfa * 0.1)
        
        # Normalize to 0-1
        return min(risk, 1.0)
    
    def _calculate_risk_score(self, factors: RiskFactors) -> float:
        """Calculate overall risk score using weighted factors"""
        
        # Weights (higher weights = more important)
        weights = {
            'biometric': 0.3,  # Biometric accuracy is critical
            'behavioral': 0.2,
            'device': 0.15,
            'location': 0.15,
            'time': 0.1,
            'network': 0.05,
            'attempt_history': 0.05
        }
        
        # Convert scores to risk (1.0 - score)
        risk_score = (
            (1.0 - factors.biometric_score) * weights['biometric'] +
            (1.0 - factors.behavioral_score) * weights['behavioral'] +
            factors.device_score * weights['device'] +
            factors.location_score * weights['location'] +
            factors.time_score * weights['time'] +
            factors.network_score * weights['network'] +
            factors.attempt_history_score * weights['attempt_history']
        )
        
        # Convert to 0-100 scale
        return risk_score * 100
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score < 30:
            return "LOW"
        elif risk_score < 70:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_confidence(self, factors: RiskFactors) -> float:
        """Calculate confidence in risk assessment"""
        # Average of all factor confidences
        avg = (
            factors.biometric_score +
            factors.behavioral_score +
            factors.device_score +
            factors.location_score +
            factors.time_score +
            factors.network_score +
            factors.attempt_history_score
        ) / 7.0
        
        return avg
    
    def _get_recommended_action(self, risk_level: str, factors: RiskFactors) -> str:
        """Get recommended action based on risk"""
        
        if risk_level == "LOW":
            return "ALLOW_AUTHENTICATION"
        elif risk_level == "MEDIUM":
            if factors.behavioral_score < 0.6 or factors.location_score > 0.5:
                return "REQUIRE_MFA"
            else:
                return "ALLOW_WITH_MONITORING"
        else:  # HIGH
            if factors.biometric_score < 0.5:
                return "DENY_AUTHENTICATION"
            else:
                return "REQUIRE_ADDITIONAL_VERIFICATION"
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
