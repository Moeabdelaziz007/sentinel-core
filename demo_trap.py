#!/usr/bin/env python3
"""Demonstration of Sentinel Trap functionality"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from trap.injector import TrapInjector, InjectionContext
from trap.honeytokens import TokenType


def demo_trap_injection():
    """Demonstrate honeytoken injection functionality"""
    print("🪤 SENTINEL TRAP DEMO")
    print("=" * 50)
    
    # Initialize trap injector
    injector = TrapInjector()
    
    # Test prompt
    original_prompt = "Write a Python script to connect to our database and fetch user records."
    
    print(f"Original Prompt: {original_prompt}")
    print()
    
    # Test different injection contexts
    contexts = [
        (InjectionContext.SYSTEM, "System Context Injection"),
        (InjectionContext.USER, "User Context Injection"), 
        (InjectionContext.CODE, "Code Context Injection"),
        (InjectionContext.COMMENT, "Comment Context Injection")
    ]
    
    for context, description in contexts:
        print(f"{description}:")
        print("-" * 30)
        
        # Inject honeytoken
        injected_text, token_id = injector.inject_honeytoken(
            original_prompt, 
            context=context
        )
        
        print(f"Injected Text:\n{injected_text}")
        print(f"Token ID: {token_id}")
        print()
    
    # Show all injected tokens
    print("TRACKED HONEYTOKENS:")
    print("-" * 20)
    tokens = injector.get_injected_tokens()
    for token_id, info in tokens.items():
        print(f"ID: {token_id}")
        print(f"Type: {info['type']}")
        print(f"Created: {info['created']}")
        print()


def demo_token_detection():
    """Demonstrate honeytoken detection when stolen"""
    print("🕵️ HONEYTOKEN DETECTION DEMO")
    print("=" * 40)
    
    injector = TrapInjector()
    
    # Create a test scenario
    prompt = "Help me debug this API connection issue"
    injected_prompt, token_id = injector.inject_honeytoken(
        prompt, 
        context=InjectionContext.SYSTEM
    )
    
    print(f"Injected Prompt: {injected_prompt}")
    print()
    
    # Simulate an attacker stealing and using the token
    stolen_token = "sk-proj-89s8xyz123abc"  # This would be from the actual injected token
    
    # Check if token usage is detected
    detection_result = injector.check_token_usage(stolen_token)
    
    if detection_result:
        print("🚨 ATTACK DETECTED!")
        print(f"Triggered tokens: {detection_result}")
    else:
        print("✅ No suspicious activity detected")


if __name__ == "__main__":
    try:
        demo_trap_injection()
        demo_token_detection()
        
        print("✅ Trap demo completed successfully!")
        print("🎯 Ready for integration with Shield system")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)