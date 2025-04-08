# This script helps Claude DC manage his API token usage with Anthropic's Claude Computer Use feature.
# Purpose: Prevent Claude DC from exceeding his API rate limits by monitoring token usage after each API call
#          and introducing delays when limits are close to being hit. This ensures efficient operation without
#          slowing down unnecessarily, by pacing tasks based on real-time limit data.
#
# How it works:
# 1. After each API call, the script checks the response headers for remaining tokens (input, output, and total).
# 2. If any token type falls below 20% of its limit, it calculates a delay until the limit resets and pauses execution.
# 3. This allows Claude DC to continue working on tasks without hitting limits, adjusting his pace dynamically.
#
# How Claude DC can utilize it:
# - Integrate this into his API-calling routine by passing response headers to `check_token_limits` after each call.
# - If a delay is needed, pause operations (e.g., sleep) for the specified time before the next call.
# - This can be used in a loop, event-driven system, or wrapped around his API call function.
#
# Requirements: Python 3.x with standard libraries (time, datetime).

import time
import datetime

fib_sequence = [1, 1, 2, 3, 5, 8, 13]
delay_count = 0

def parse_reset_time(reset_time_str):
    """
    Parse the reset time from ISO 8601 format (e.g., '2025-04-07T23:05:10Z') into a datetime object.
    
    Args:
        reset_time_str (str): The reset time string from the API headers.
    
    Returns:
        datetime.datetime: The parsed reset time in UTC.
    """
    # Replace 'Z' with '+00:00' for proper ISO 8601 parsing
    reset_time = datetime.datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
    return reset_time

def calculate_delay(reset_time):
    """
    Calculate the seconds to delay until the reset time, ensuring no negative delays.
    
    Args:
        reset_time (datetime.datetime): The reset time from the headers.
    
    Returns:
        float: Delay in seconds (non-negative).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    delay = (reset_time - now).total_seconds()
    return max(delay, 0)

def check_token_limits(headers):
    """
    Check token usage against thresholds and determine if a delay is needed.
    
    Args:
        headers (dict): The API response headers with rate limit info.
    
    Returns:
        tuple: (should_delay: bool, delay_time: float)
               - should_delay: True if a delay is needed, False otherwise.
               - delay_time: Seconds to delay if True, 0 if False.
    """
    # Extract remaining tokens and limits from headers
    input_remaining = int(headers['anthropic-ratelimit-input-tokens-remaining'])
    output_remaining = int(headers['anthropic-ratelimit-output-tokens-remaining'])
    tokens_remaining = int(headers['anthropic-ratelimit-tokens-remaining'])
    
    input_limit = int(headers['anthropic-ratelimit-input-tokens-limit'])
    output_limit = int(headers['anthropic-ratelimit-output-tokens-limit'])
    tokens_limit = int(headers['anthropic-ratelimit-tokens-limit'])
    
    # Extract reset times
    input_reset = parse_reset_time(headers['anthropic-ratelimit-input-tokens-reset'])
    output_reset = parse_reset_time(headers['anthropic-ratelimit-output-tokens-reset'])
    tokens_reset = parse_reset_time(headers['anthropic-ratelimit-tokens-reset'])
    
    # Define thresholds as 10% of each limit
    input_threshold = 0.2 * input_limit
    output_threshold = 0.2 * output_limit
    tokens_threshold = 0.2 * tokens_limit
    
    # Check if any token type is below its threshold
    if input_remaining < input_threshold:
        delay = calculate_delay(input_reset)
        print(f"Input tokens low ({input_remaining}/{input_limit}). Delaying for {delay:.2f} seconds.")
        return True, delay
    if output_remaining < output_threshold:
        delay = calculate_delay(output_reset)
        print(f"Output tokens low ({output_remaining}/{output_limit}). Delaying for {delay:.2f} seconds.")
        return True, delay
    if tokens_remaining < tokens_threshold:
        delay = calculate_delay(tokens_reset)
        print(f"Total tokens low ({tokens_remaining}/{tokens_limit}). Delaying for {delay:.2f} seconds.")
        return True, delay
    return False, 0  # No delay needed

# Example usage:
# Assuming you have a function `make_api_call(payload)` that returns a response with headers
"""
# Example loop integrating the script with Fibonacci backoff
payloads = ["task1", "task2", "task3"]  # Replace with your actual payloads
for payload in payloads:
    response = make_api_call(payload)  # Your API call function
    should_delay, delay_time = check_token_limits(response.headers)
    if should_delay:
        # Use Fibonacci backoff for delay time
        if delay_count < len(fib_sequence):
            delay_time = fib_sequence[delay_count]
            delay_count += 1
        else:
            delay_time = fib_sequence[-1]  # Cap at the last Fibonacci number
        logger.info(f"Pausing for {delay_time} seconds due to low token limits...")
        time.sleep(delay_time)
    else:
        delay_count = 0  # Reset delay count if no delay is needed
"""
