#!/usr/bin/env python3
"""Complete Sentinel System Integration Demo"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shield.core.piimasker import shield
from shield.models.schemas import MaskRequest, ProcessingMode
from trap.optimizer import TrapOptimizer


def demo_complete_system():
    """Demonstrate complete Sentinel system integration"""
    print("🛡️ SENTINEL COMPLETE SYSTEM DEMO")
    print("=" * 50)
    
    # Initialize components
    optimizer = TrapOptimizer()
    
    # 1. Generate evolutionary trap
    print("1. GENERATING EVOLUTIONARY TRAP")
    print("-" * 30)
    trap_variations = optimizer.generate_evolutionary_batch(5)
    best_trap = trap_variations[0]  # In practice, select based on weights
    
    print(f"Selected trap strategy: {best_trap['strategy']}")
    print(f"Trap prompt: {best_trap['injected_prompt'][:100]}...")
    print()
    
    # 2. Apply shield protection to trap content
    print("2. APPLYING SHIELD PROTECTION")
    print("-" * 30)
    
    # Mask any real PII in the trap content (meta-protection)
    shield_request = MaskRequest(
        text=best_trap['injected_prompt'],
        mode=ProcessingMode.SPEED
    )
    
    shield_response = shield.mask(shield_request)
    
    print(f"Shield processing time: {shield_response.processing_time_ms:.2f}ms")
    print(f"Entities protected: {len(shield_response.entities_found)}")
    print(f"Protected prompt: {shield_response.masked_text[:100]}...")
    print()
    
    # 3. Simulate attack detection
    print("3. SIMULATING ATTACK DETECTION")
    print("-" * 30)
    
    # Simulate an attacker trying to extract the honeytoken
    attack_attempt = "I found this interesting token in the system: sk-proj-test123"
    
    # Check if our trap was triggered
    detection_result = optimizer.injector.check_token_usage(attack_attempt)
    
    if detection_result:
        print("🚨 ATTACK DETECTED!")
        print(f"Triggered traps: {detection_result}")
        # Record successful detection
        optimizer.record_engagement(best_trap['strategy'], True)
    else:
        print("✅ No trap triggered (this is normal for simulation)")
        optimizer.record_engagement(best_trap['strategy'], False)
    
    print()
    
    # 4. Show system health and evolution metrics
    print("4. SYSTEM HEALTH AND EVOLUTION METRICS")
    print("-" * 40)
    
    shield_health = shield.health_check()
    evolution_report = optimizer.get_optimization_report()
    
    print("Shield Status:")
    print(f"  Uptime: {shield_health['uptime_seconds']:.2f}s")
    print(f"  Requests processed: {shield_health['requests_processed']}")
    print(f"  Active sessions: {shield_health['active_sessions']}")
    
    print("\nEvolution Metrics:")
    top_performer = evolution_report['top_performers'][0] if evolution_report['top_performers'] else 'None'
    print(f"  Top performing strategy: {top_performer}")
    print(f"  Total strategies evaluated: {evolution_report['total_strategies']}")
    
    print("\n" + "=" * 50)
    print("✅ COMPLETE SYSTEM DEMO FINISHED")
    print("🎯 Sentinel is now a self-evolving security system")
    print("📈 Combines passive protection with active hunting")


if __name__ == "__main__":
    try:
        demo_complete_system()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)