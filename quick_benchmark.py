#!/usr/bin/env python3
"""Quick performance benchmark for Sentinel Shield"""

import sys
import os
import time
import statistics

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shield.core.piimasker import shield
from shield.models.schemas import MaskRequest, ProcessingMode

def run_quick_benchmark():
    print("🛡️ SENTINEL SHIELD QUICK BENCHMARK")
    print("=" * 40)
    
    # Test cases
    test_cases = [
        ("Simple Email", "Contact john@example.com"),
        ("Medium PII", "Email: user@test.com, Phone: (555) 123-4567"),
        ("Complex Document", "Customer service@company.com ordered item #12345. Card: 4532-1234-5678-9012. API: sk_abcdef123456")
    ]
    
    # Test each mode
    for mode in [ProcessingMode.SPEED, ProcessingMode.BALANCED]:
        print(f"\n{mode.value.upper()} MODE:")
        print("-" * 20)
        
        latencies = []
        for name, text in test_cases:
            request = MaskRequest(text=text, mode=mode)
            
            # Run 10 iterations for accuracy
            times = []
            for _ in range(10):
                start = time.perf_counter()
                response = shield.mask(request)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            p95_time = sorted(times)[8]  # 90th percentile approximation
            latencies.append(avg_time)
            
            print(f"{name:15}: {avg_time:6.2f}ms avg, {p95_time:6.2f}ms p95")
        
        overall_avg = statistics.mean(latencies)
        print(f"Overall Average: {overall_avg:.2f}ms")
    
    # Throughput test
    print(f"\nTHROUGHPUT TEST:")
    print("-" * 20)
    
    test_text = "Contact support@company.com or call (555) 123-4567"
    request = MaskRequest(text=test_text, mode=ProcessingMode.BALANCED)
    
    # Warm up
    for _ in range(5):
        shield.mask(request)
    
    # Measure throughput
    start_time = time.time()
    requests_completed = 0
    duration = 5.0  # 5 seconds
    
    while time.time() - start_time < duration:
        shield.mask(request)
        requests_completed += 1
    
    elapsed = time.time() - start_time
    throughput = requests_completed / elapsed
    
    print(f"Completed {requests_completed} requests in {elapsed:.2f} seconds")
    print(f"Throughput: {throughput:.1f} requests/second")

if __name__ == "__main__":
    run_quick_benchmark()