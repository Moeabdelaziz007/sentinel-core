#!/usr/bin/env python3
"""Performance benchmarking for Sentinel Shield"""

import time
import statistics
from typing import List, Dict, Any
import asyncio
import aiohttp

from src.shield.core.piimasker import shield
from src.shield.models.schemas import MaskRequest, ProcessingMode


class ShieldBenchmark:
    """Benchmark suite for Sentinel Shield performance"""
    
    def __init__(self):
        self.test_cases = self._generate_test_cases()
    
    def _generate_test_cases(self) -> List[Dict[str, Any]]:
        """Generate various test cases for benchmarking"""
        return [
            {
                "name": "Short Email Only",
                "text": "Contact me at john.doe@example.com for more info",
                "expected_entities": 1,
                "size_category": "small"
            },
            {
                "name": "Medium Mixed PII",
                "text": (
                    "Customer John Smith (john@test.com) ordered "
                    "item #12345. Credit card: 4532-1234-5678-9012. "
                    "Phone: (555) 123-4567"
                ),
                "expected_entities": 4,
                "size_category": "medium"
            },
            {
                "name": "Long Document",
                "text": (
                    "Dear Customer Service, I am writing to report "
                    "an issue with my account. My email is "
                    "customer.service@company.com and my phone "
                    "number is +1-555-0123. My credit card ending "
                    "in 9012 was charged incorrectly. API Key: "
                    "sk_abcdefghijklmnopqrstuvwxyz123456. SSN: "
                    "123-45-6789. Please investigate this matter."
                ),
                "expected_entities": 5,
                "size_category": "large"
            },
            {
                "name": "High Density PII",
                "text": (
                    "Multiple emails: admin@site.com, "
                    "user@test.org, support@help.net. Cards: "
                    "4532123456789012, 5555555555554444, "
                    "378282246310005. Phones: 555-0100, "
                    "555-0101, 555-0102"
                ),
                "expected_entities": 8,
                "size_category": "high_density"
            }
        ]
    
    def run_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        print("🛡️ Running Sentinel Shield Performance Benchmarks")
        print("=" * 50)
        
        results = {
            "summary": {},
            "detailed": [],
            "performance_targets": {
                "latency_avg_ms": "<5",
                "latency_95th_percentile_ms": "<10",
                "throughput_req_per_sec": ">100"
            }
        }
        
        # Test each processing mode
        for mode in [ProcessingMode.SPEED, ProcessingMode.BALANCED]:
            print(f"\nTesting {mode.value.upper()} mode:")
            print("-" * 30)
            
            mode_results = self._benchmark_mode(mode)
            results["detailed"].append({
                "mode": mode.value,
                "results": mode_results
            })
        
        # Calculate summary statistics
        results["summary"] = self._calculate_summary(results["detailed"])
        
        self._print_results(results)
        return results
    
    def _benchmark_mode(self, mode: ProcessingMode) -> Dict[str, Any]:
        """Benchmark a specific processing mode"""
        latencies = []
        throughput_tests = []
        
        # Latency tests
        print("Running latency tests...")
        for test_case in self.test_cases:
            request = MaskRequest(
                text=test_case["text"],
                mode=mode
            )
            
            # Run multiple iterations for accurate timing
            iteration_times = []
            for _ in range(10):
                start_time = time.perf_counter()
                try:
                    response = shield.mask(request)
                    elapsed = (time.perf_counter() - start_time) * 1000
                    iteration_times.append(elapsed)
                except Exception as e:
                    print(f"Error in {test_case['name']}: {e}")
                    iteration_times.append(float('inf'))
            
            avg_latency = statistics.mean(iteration_times)
            p95_latency = statistics.quantiles(iteration_times, n=20)[18]  # 95th percentile
            
            latencies.append({
                "test_case": test_case["name"],
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "entities_found": len(response.entities_found) if 'response' in locals() else 0
            })
            
            print(f"  {test_case['name']}: {avg_latency:.2f}ms avg, {p95_latency:.2f}ms p95")
        
        # Throughput test
        print("Running throughput test...")
        throughput_result = self._test_throughput(mode)
        throughput_tests.append(throughput_result)
        
        return {
            "latency_tests": latencies,
            "throughput_tests": throughput_tests
        }
    
    def _test_throughput(self, mode: ProcessingMode) -> Dict[str, Any]:
        """Test throughput performance"""
        test_text = self.test_cases[1]["text"]  # Medium test case
        request = MaskRequest(text=test_text, mode=mode)
        
        # Warm up
        for _ in range(5):
            shield.mask(request)
        
        # Actual throughput test
        start_time = time.time()
        requests_completed = 0
        test_duration = 5.0  # 5 seconds
        
        while time.time() - start_time < test_duration:
            shield.mask(request)
            requests_completed += 1
        
        elapsed = time.time() - start_time
        throughput = requests_completed / elapsed
        
        return {
            "requests_completed": requests_completed,
            "test_duration_seconds": elapsed,
            "throughput_req_per_sec": throughput
        }
    
    def _calculate_summary(self, detailed_results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        all_latencies = []
        all_throughput = []
        
        for mode_result in detailed_results:
            for latency_test in mode_result["results"]["latency_tests"]:
                all_latencies.append(latency_test["avg_latency_ms"])
            for throughput_test in mode_result["results"]["throughput_tests"]:
                all_throughput.append(throughput_test["throughput_req_per_sec"])
        
        if not all_latencies:
            return {}
        
        return {
            "overall_avg_latency_ms": statistics.mean(all_latencies),
            "overall_p95_latency_ms": statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) > 1 else max(all_latencies),
            "overall_throughput_req_per_sec": statistics.mean(all_throughput) if all_throughput else 0,
            "total_test_cases": len(all_latencies)
        }
    
    def _print_results(self, results: Dict[str, Any]):
        """Print formatted benchmark results"""
        print("\n" + "=" * 50)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 50)
        
        summary = results["summary"]
        if summary:
            print(f"Overall Average Latency: {summary['overall_avg_latency_ms']:.2f}ms")
            print(f"95th Percentile Latency: {summary['overall_p95_latency_ms']:.2f}ms")
            print(f"Average Throughput: {summary['overall_throughput_req_per_sec']:.1f} req/sec")
            print(f"Total Test Cases: {summary['total_test_cases']}")
        
        print("\nPerformance Targets:")
        targets = results["performance_targets"]
        for metric, target in targets.items():
            print(f"  {metric}: {target}")


async def run_async_benchmark():
    """Run async benchmark against the API"""
    print("\n📡 Running API benchmark...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        async with session.get('http://localhost:8000/health') as resp:
            health = await resp.json()
            print(f"API Health: {health}")
        
        # Test masking endpoint
        test_data = {
            "text": "Contact john@example.com for credit card 4532123456789012",
            "mode": "balanced"
        }
        
        start_time = time.time()
        async with session.post('http://localhost:8000/mask', json=test_data) as resp:
            result = await resp.json()
            api_latency = (time.time() - start_time) * 1000
            print(f"API Latency: {api_latency:.2f}ms")
            print(f"Entities Found: {len(result.get('entities_found', []))}")


if __name__ == "__main__":
    # Run local benchmark
    benchmark = ShieldBenchmark()
    results = benchmark.run_benchmark()
    
    # If API is running, also test async performance
    try:
        asyncio.run(run_async_benchmark())
    except Exception as e:
        print(f"API benchmark skipped: {e}")