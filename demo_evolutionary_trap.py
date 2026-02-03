#!/usr/bin/env python3
"""Demonstration of Evolutionary Trap System (AlphaEvolve concept)"""

import sys
import os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from trap.optimizer import TrapOptimizer
from trap.honeytokens import TokenType


def demo_evolutionary_generation():
    """Demonstrate evolutionary trap generation"""
    print("🧬 EVOLUTIONARY TRAP GENERATION DEMO")
    print("=" * 50)
    
    optimizer = TrapOptimizer()
    
    # Generate evolutionary batch
    print("Generating 20 trap variations using weighted strategies...")
    variations = optimizer.generate_evolutionary_batch(20)
    
    # Show sample variations
    print("\nSAMPLE TRAP VARIATIONS:")
    print("-" * 30)
    
    for i, variation in enumerate(variations[:5]):
        print(f"\nVariation {i+1}:")
        print(f"Strategy: {variation['strategy']}")
        print(f"Token Type: {variation['token_type']}")
        print(f"Injected Prompt:\n{variation['injected_prompt'][:100]}...")
        print()


def demo_strategy_performance():
    """Demonstrate strategy performance tracking"""
    print("📊 STRATEGY PERFORMANCE DEMO")
    print("=" * 40)
    
    optimizer = TrapOptimizer()
    
    # Simulate engagements with different outcomes
    strategies = [
        "system_comment", "user_history", "json_leak", 
        "code_comment", "environment_var"
    ]
    
    print("Simulating trap engagements...")
    
    # Record some successful detections
    for strategy in strategies:
        # Simulate 3-7 deployments per strategy
        deployments = random.randint(3, 7)
        successes = random.randint(1, deployments)
        
        for _ in range(deployments):
            was_detected = random.random() < (successes / deployments)
            optimizer.record_engagement(strategy, was_detected)
    
    # Show performance report
    report = optimizer.get_optimization_report()
    
    print("\nSTRATEGY PERFORMANCE REPORT:")
    print("-" * 35)
    
    performance = report["strategy_performance"]
    sorted_strategies = sorted(
        performance.items(), 
        key=lambda x: x[1]["success_rate"], 
        reverse=True
    )
    
    for strategy, metrics in sorted_strategies:
        print(f"{strategy:15} | "
              f"Rate: {metrics['success_rate']:.2f} | "
              f"Weight: {metrics['current_weight']:.2f} | "
              f"Detections: {metrics['successful_detections']}/{metrics['total_deployments']}")


def demo_adaptive_selection():
    """Demonstrate adaptive strategy selection"""
    print("\n🎯 ADAPTIVE STRATEGY SELECTION")
    print("=" * 35)
    
    optimizer = TrapOptimizer()
    
    # Simulate initial engagements to establish baselines
    print("Establishing initial performance baselines...")
    
    # Make some strategies obviously better
    good_strategies = ["json_leak", "user_history"]
    poor_strategies = ["system_comment", "code_comment"]
    
    # Train good strategies
    for strategy in good_strategies:
        for _ in range(10):
            optimizer.record_engagement(strategy, True)  # High success rate
    
    # Train poor strategies  
    for strategy in poor_strategies:
        for _ in range(10):
            optimizer.record_engagement(strategy, False)  # Low success rate
    
    # Generate new batch with learned weights
    print("\nGenerating new batch with adaptive selection...")
    variations = optimizer.generate_evolutionary_batch(50)
    
    # Count strategy distribution
    strategy_counts = {}
    for variation in variations:
        strategy = variation["strategy"]
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    print("\nSTRATEGY USAGE DISTRIBUTION:")
    print("-" * 30)
    for strategy, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / 50) * 100
        print(f"{strategy:15}: {count:2d} ({percentage:5.1f}%)")


def demo_red_team_simulation():
    """Simulate red team attack detection"""
    print("\n⚔️ RED TEAM SIMULATION")
    print("=" * 25)
    
    optimizer = TrapOptimizer()
    
    # Create test scenario
    test_prompt = "Write a script to backup our production database"
    variation = optimizer.generate_evolutionary_batch(1)[0]
    
    print(f"Test Prompt: {test_prompt}")
    print(f"Injection Strategy: {variation['strategy']}")
    print(f"Injected Content: ...{variation['injected_prompt'][-100:]}")
    
    # Simulate red team detection
    # In reality, this would involve an LLM trying to extract credentials
    simulated_detection = random.random() < 0.7  # 70% detection rate
    
    if simulated_detection:
        print("🚨 RED TEAM DETECTED THE TRAP!")
        optimizer.record_engagement(variation['strategy'], True)
    else:
        print("✅ Trap remained undetected")
        optimizer.record_engagement(variation['strategy'], False)


if __name__ == "__main__":
    try:
        demo_evolutionary_generation()
        demo_strategy_performance()
        demo_adaptive_selection()
        demo_red_team_simulation()
        
        print("\n" + "=" * 50)
        print("✅ Evolutionary Trap Demo Completed!")
        print("🎯 System demonstrates Darwinian security principles")
        print("📈 Ready for continuous improvement cycle")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)