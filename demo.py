#!/usr/bin/env python3
"""Demonstration of Sentinel Shield functionality"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shield.core.piimasker import shield
from shield.models.schemas import MaskRequest, ProcessingMode


def demo_basic_masking():
    """Demonstrate basic PII masking functionality"""
    print("🛡️ SENTINEL SHIELD DEMO")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Email Protection",
            "text": "Please contact john.doe@company.com for assistance",
            "mode": ProcessingMode.SPEED
        },
        {
            "name": "Credit Card Protection", 
            "text": "My card number is 4532-1234-5678-9012",
            "mode": ProcessingMode.BALANCED
        },
        {
            "name": "Mixed PII Protection",
            "text": "Customer: Jane Smith, Email: jane@test.com, Phone: (555) 123-4567, CC: 5555-5555-5555-4444",
            "mode": ProcessingMode.ACCURACY
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")
        print(f"   Original: {test_case['text']}")
        
        # Create mask request
        request = MaskRequest(
            text=test_case['text'],
            mode=test_case['mode']
        )
        
        # Perform masking
        response = shield.mask(request)
        
        print(f"   Masked:   {response.masked_text}")
        print(f"   Mode:     {response.mode_used.value}")
        print(f"   Time:     {response.processing_time_ms:.2f}ms")
        print(f"   Entities: {len(response.entities_found)}")
        
        # Show entity details
        if response.entities_found:
            print("   Detected Entities:")
            for entity in response.entities_found:
                print(f"     - {entity.entity_type.value}: {entity.original_text} → {entity.masked_text} ({entity.confidence:.2f})")
        
        # Demonstrate unmasking
        if response.session_id and response.entities_found:
            print(f"   Unmasking with session {response.session_id}...")
            from shield.models.schemas import UnmaskRequest
            unmask_request = UnmaskRequest(
                masked_text=response.masked_text,
                session_id=response.session_id
            )
            unmask_response = shield.unmask(unmask_request)
            print(f"   Restored: {unmask_response.original_text}")


def demo_performance_comparison():
    """Compare performance across different modes"""
    print("\n" + "=" * 50)
    print("PERFORMANCE COMPARISON")
    print("=" * 50)
    
    test_text = "Contact support@company.com or call (555) 123-4567. Card: 4532-1234-5678-9012"
    
    for mode in [ProcessingMode.SPEED, ProcessingMode.BALANCED, ProcessingMode.ACCURACY]:
        request = MaskRequest(text=test_text, mode=mode)
        
        # Run multiple times for average
        times = []
        for _ in range(5):
            response = shield.mask(request)
            times.append(response.processing_time_ms)
        
        avg_time = sum(times) / len(times)
        print(f"{mode.value.upper():>10}: {avg_time:>6.2f}ms (avg of 5 runs)")


def demo_health_check():
    """Show system health information"""
    print("\n" + "=" * 50)
    print("SYSTEM HEALTH")
    print("=" * 50)
    
    health = shield.health_check()
    for key, value in health.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    try:
        demo_basic_masking()
        demo_performance_comparison()
        demo_health_check()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("🎯 Ready for production deployment")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)