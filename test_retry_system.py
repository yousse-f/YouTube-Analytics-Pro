#!/usr/bin/env python3
"""
Test script per verificare il sistema di retry implementato.
"""

import asyncio
import time
from app.utils.retry import retry_http_calls, retry_external_calls, with_retry_logging
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MockFailureException(Exception):
    """Mock exception for testing retry behavior"""
    pass


# Contatore per testare i retry
attempt_counter = 0


@retry_external_calls
@with_retry_logging
def failing_function_with_retry():
    """Funzione che fallisce le prime 2 volte, poi ha successo"""
    global attempt_counter
    attempt_counter += 1
    
    logger.info(f"Attempt #{attempt_counter}")
    
    if attempt_counter <= 2:
        raise MockFailureException(f"Simulated failure on attempt {attempt_counter}")
    
    return f"Success on attempt {attempt_counter}!"


def test_retry_mechanism():
    """Test del meccanismo di retry"""
    global attempt_counter
    
    print("🧪 Testing retry mechanism...")
    print("=" * 50)
    
    # Reset counter
    attempt_counter = 0
    
    try:
        result = failing_function_with_retry()
        print(f"✅ Function succeeded: {result}")
        print(f"📊 Total attempts made: {attempt_counter}")
        
        if attempt_counter == 3:
            print("✅ Retry mechanism working correctly (failed 2 times, succeeded on 3rd)")
        else:
            print(f"⚠️ Unexpected retry behavior (expected 3 attempts, got {attempt_counter})")
            
    except Exception as e:
        print(f"❌ Function failed even with retries: {e}")
        print(f"📊 Total attempts made: {attempt_counter}")


@retry_external_calls
@with_retry_logging
def always_failing_function():
    """Funzione che fallisce sempre per testare l'esaurimento dei retry"""
    global attempt_counter
    attempt_counter += 1
    
    logger.warning(f"Always failing attempt #{attempt_counter}")
    raise MockFailureException(f"Always fails - attempt {attempt_counter}")


def test_retry_exhaustion():
    """Test dell'esaurimento dei retry"""
    global attempt_counter
    
    print("\n🧪 Testing retry exhaustion...")
    print("=" * 50)
    
    # Reset counter
    attempt_counter = 0
    
    try:
        result = always_failing_function()
        print(f"❌ Unexpected success: {result}")
    except MockFailureException as e:
        print(f"✅ Function failed as expected after retries: {e}")
        print(f"📊 Total attempts made: {attempt_counter}")
        
        # Verifico che sia stato fatto il numero corretto di tentativi
        # (1 tentativo iniziale + N retry = RETRY_ATTEMPTS totali)
        from app.config import Settings
        settings = Settings()
        expected_attempts = settings.RETRY_ATTEMPTS
        
        if attempt_counter == expected_attempts:
            print(f"✅ Retry exhaustion working correctly ({expected_attempts} attempts)")
        else:
            print(f"⚠️ Unexpected retry behavior (expected {expected_attempts} attempts, got {attempt_counter})")


def test_configuration():
    """Test della configurazione del retry"""
    print("\n🧪 Testing retry configuration...")
    print("=" * 50)
    
    from app.config import Settings
    settings = Settings()
    
    print(f"📋 Retry Configuration:")
    print(f"   - Max attempts: {settings.RETRY_ATTEMPTS}")
    print(f"   - Initial wait: {settings.RETRY_WAIT_SECONDS}s")
    print(f"   - Backoff multiplier: {settings.RETRY_BACKOFF_MULTIPLIER}")
    print(f"   - Max wait: {settings.RETRY_MAX_WAIT_SECONDS}s")
    
    # Calcolo la progressione del backoff
    wait_times = []
    current_wait = settings.RETRY_WAIT_SECONDS
    
    for i in range(settings.RETRY_ATTEMPTS - 1):
        wait_times.append(min(current_wait, settings.RETRY_MAX_WAIT_SECONDS))
        current_wait *= settings.RETRY_BACKOFF_MULTIPLIER
    
    print(f"📈 Expected wait times between retries: {wait_times}")


if __name__ == "__main__":
    print("🚀 Starting Retry System Test")
    print("=" * 60)
    
    try:
        # Test configurazione
        test_configuration()
        
        # Test retry con successo
        test_retry_mechanism()
        
        # Test esaurimento retry
        test_retry_exhaustion()
        
        print("\n" + "=" * 60)
        print("✅ All retry system tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
