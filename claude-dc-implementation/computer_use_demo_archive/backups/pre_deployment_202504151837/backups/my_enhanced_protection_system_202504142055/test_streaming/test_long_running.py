#!/usr/bin/env python3
"""
Test Script for Long-Running Operations (10+ minutes)

This script specifically tests the enhanced streaming client's ability to handle
very long-running operations that exceed 10 minutes, which is critical for
ensuring continuous operation without timeouts.
"""

import os
import sys
import time
import logging
import threading
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/long_running_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("long_running_test")

# Import the enhanced streaming client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from streaming_client import streaming_client

# Import token manager if available
try:
    sys.path.append('/home/computeruse/computer_use_demo')
    from token_management.token_manager import token_manager
    has_token_manager = True
    logger.info("Token manager found and imported")
except ImportError:
    has_token_manager = False
    logger.warning("Token manager not found, proceeding without token management")

def log_stats(stats_file, data):
    """Log statistics to a CSV file"""
    with open(stats_file, 'a') as f:
        f.write(f"{data['timestamp']},{data['elapsed']},{data['chunks']},{data['chars']},"
               f"{data['input_tokens']},{data['output_tokens']}\n")

def simulate_long_running_operation(duration_minutes=12, stats_interval=30):
    """Simulate a long-running operation with streaming
    
    Args:
        duration_minutes: Target duration in minutes
        stats_interval: Interval for logging stats in seconds
    """
    print(f"\n===== Simulating Long-Running Operation ({duration_minutes} minutes) =====")
    
    # Create a stats file
    stats_file = f"/tmp/long_running_stats_{int(time.time())}.csv"
    with open(stats_file, 'w') as f:
        f.write("timestamp,elapsed_seconds,chunks,chars,input_tokens,output_tokens\n")
    
    # Create a prompt designed to generate a very long response
    prompt = """
Please create a comprehensive guide on artificial intelligence and machine learning. 
The guide should cover the following topics in extensive detail:

1. History of AI and Machine Learning
   - Early developments and key milestones
   - Major paradigm shifts over time
   - Key figures and their contributions

2. Fundamental Concepts
   - Types of machine learning (supervised, unsupervised, reinforcement)
   - Neural networks and deep learning
   - Feature engineering and selection
   - Training, validation, and testing methodology

3. Modern AI Applications
   - Natural language processing
   - Computer vision
   - Recommendation systems
   - Autonomous systems
   - Healthcare applications
   - Financial applications

4. Technical Implementation
   - Popular frameworks and libraries
   - Hardware considerations (CPU vs GPU vs TPU)
   - Scaling and distributed training
   - Model deployment strategies

5. Ethical Considerations
   - Bias and fairness in AI
   - Privacy concerns
   - Transparency and explainability
   - Societal impact and considerations

6. Future Directions
   - Emerging research areas
   - Anticipated breakthroughs
   - Challenges and limitations

For each section, please provide detailed explanations, examples, and references to important research or applications.
This should be a comprehensive resource that covers both theoretical foundations and practical aspects.
"""
    
    # Stats for tracking
    chunks_received = 0
    chars_received = 0
    last_stats_time = time.time()
    start_time = time.time()
    
    def stream_callback(chunk):
        nonlocal chunks_received, chars_received, last_stats_time
        chunks_received += 1
        chars_received += len(chunk)
        
        # Update progress periodically
        current_time = time.time()
        elapsed = current_time - start_time
        if current_time - last_stats_time >= stats_interval or chunks_received % 100 == 0:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            print(f"Progress: {minutes:02d}:{seconds:02d} elapsed, {chunks_received} chunks, {chars_received} chars")
            
            # Log stats
            if has_token_manager:
                stats = {
                    "timestamp": datetime.now().isoformat(),
                    "elapsed": elapsed,
                    "chunks": chunks_received,
                    "chars": chars_received,
                    "input_tokens": token_manager.input_tokens_per_minute,
                    "output_tokens": token_manager.output_tokens_per_minute
                }
                log_stats(stats_file, stats)
            
            last_stats_time = current_time
    
    print(f"Starting long-running operation (target: {duration_minutes} minutes)...")
    print(f"Stats will be logged to: {stats_file}")
    
    # Make the API call with streaming
    response = streaming_client.create_message(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000,  # Request a large number of tokens
        stream_callback=stream_callback,
        # Use system message to encourage a very detailed response
        system="You are an expert AI educator who provides extremely detailed, comprehensive, and thorough explanations. When asked about a topic, you explore it from multiple angles and provide extensive information."
    )
    
    total_duration = time.time() - start_time
    duration_minutes_actual = total_duration / 60
    
    # Extract content length from response
    content_length = 0
    if isinstance(response, dict) and "content" in response:
        content = response["content"]
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                full_text = content[0]["text"]
                content_length = len(full_text)
    
    print(f"\nCompleted long-running operation in {duration_minutes_actual:.2f} minutes")
    print(f"Target duration: {duration_minutes} minutes")
    print(f"Received {chunks_received} chunks, total content length: {content_length} characters")
    
    # Check token usage
    usage = streaming_client.last_token_usage
    print(f"Token usage: {usage['input']} input, {usage['output']} output")
    
    # Save a sample of the response
    if isinstance(response, dict) and "content" in response:
        content = response["content"]
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                sample_file = f"/tmp/long_running_response_sample_{int(time.time())}.txt"
                with open(sample_file, 'w') as f:
                    # Save first and last 1000 chars
                    full_text = content[0]["text"]
                    f.write("=== BEGINNING OF RESPONSE ===\n\n")
                    f.write(full_text[:1000])
                    f.write("\n\n...\n\n")
                    f.write(full_text[-1000:] if len(full_text) > 1000 else "")
                    f.write("\n\n=== END OF RESPONSE ===\n")
                print(f"Saved response sample to: {sample_file}")
    
    # Final stats
    final_stats = {
        "timestamp": datetime.now().isoformat(),
        "elapsed": total_duration,
        "chunks": chunks_received,
        "chars": chars_received,
        "input_tokens": usage["input"],
        "output_tokens": usage["output"]
    }
    log_stats(stats_file, final_stats)
    
    print(f"Test completion status: {'SUCCESS' if duration_minutes_actual >= duration_minutes * 0.9 else 'INCOMPLETE'}")
    return duration_minutes_actual >= duration_minutes * 0.9

def monitor_resources(duration_minutes):
    """Monitor system resources during the test"""
    # Run for slightly longer than the main test to ensure full coverage
    end_time = time.time() + (duration_minutes * 60 * 1.1)
    stats_file = f"/tmp/resource_stats_{int(time.time())}.csv"
    
    try:
        # Create stats file and write header
        with open(stats_file, 'w') as f:
            f.write("timestamp,cpu_percent,memory_percent,input_tokens,output_tokens\n")
        
        print(f"Resource monitoring started (logging to {stats_file})")
        
        while time.time() < end_time:
            timestamp = datetime.now().isoformat()
            
            # Get CPU and memory usage
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
            except ImportError:
                # If psutil is not available, use os.getloadavg() on Unix-like systems
                try:
                    load_avg = os.getloadavg()[0]
                    cpu_percent = load_avg * 100 / os.cpu_count() if os.cpu_count() else load_avg * 25
                    memory_percent = 0  # Can't reliably get memory without psutil
                except (AttributeError, OSError):
                    cpu_percent = 0
                    memory_percent = 0
            
            # Get token usage if available
            input_tokens = 0
            output_tokens = 0
            if has_token_manager:
                input_tokens = token_manager.input_tokens_per_minute
                output_tokens = token_manager.output_tokens_per_minute
            
            # Log stats
            with open(stats_file, 'a') as f:
                f.write(f"{timestamp},{cpu_percent},{memory_percent},{input_tokens},{output_tokens}\n")
            
            # Sleep to avoid excessive monitoring overhead
            time.sleep(15)  # Check every 15 seconds
    except Exception as e:
        logger.error(f"Error in resource monitoring: {e}")
    finally:
        print("Resource monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description="Test long-running operations with streaming")
    parser.add_argument("--duration", type=int, default=12, help="Target duration in minutes")
    parser.add_argument("--stats-interval", type=int, default=30, help="Interval for logging stats in seconds")
    parser.add_argument("--skip-monitoring", action="store_true", help="Skip resource monitoring")
    args = parser.parse_args()
    
    print(f"Starting long-running operation test (target: {args.duration} minutes)")
    
    # Start resource monitoring in a separate thread
    if not args.skip_monitoring:
        monitor_thread = threading.Thread(
            target=monitor_resources,
            args=(args.duration,)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
    
    # Run the test
    success = simulate_long_running_operation(
        duration_minutes=args.duration,
        stats_interval=args.stats_interval
    )
    
    if success:
        print("\n\u2705 Test SUCCESSFUL: Completed long-running operation without timeouts")
    else:
        print("\n\u274c Test FAILED: Operation did not run for the target duration")

if __name__ == "__main__":
    main()