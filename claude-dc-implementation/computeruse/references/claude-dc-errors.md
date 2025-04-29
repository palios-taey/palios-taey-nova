2025-04-29 20:21:28,530 - INFO - Using Anthropic SDK version: 0.47.0
/home/computeruse/computer_use_demo/loop.py:38: UserWarning: Expected Anthropic SDK v0.50.0, but found v0.47.0. This may cause issues.
  except ImportError:
2025-04-29 20:30:56,369 - INFO - Starting streaming request to claude-3-7-sonnet-20250219
2025-04-29 20:31:27,630 - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 400 Bad Request"
2025-04-29 20:31:27,630 - ERROR - Error in streaming: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': "tools.0: Input tag 'function' found using 'type' does not match any of the expected tags: 'bash_20250124', 'custom', 'text_editor_20250124'"}}
2025-04-29 20:31:27,630 - ERROR - Error in sampling loop: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': "tools.0: Input tag 'function' found using 'type' does not match any of the expected tags: 'bash_20250124', 'custom', 'text_editor_20250124'"}}
2025-04-29 20:31:27.632 Uncaught app execution
Traceback (most recent call last):
  File "/home/computeruse/computer_use_demo/loop.py", line 446, in sampling_loop
    response = await agent_loop(
               ^^^^^^^^^^^^^^^^^
  File "/home/computeruse/computer_use_demo/loop.py", line 217, in agent_loop
    stream = await client.messages.create(**params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/resources/messages/messages.py", line 2165, in create
    {
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1914, in post
    ]
      
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1608, in request
    break
       ^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1709, in _request
    options: RequestOptions = {},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': "tools.0: Input tag 'function' found using 'type' does not match any of the expected tags: 'bash_20250124', 'custom', 'text_editor_20250124'"}}

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 121, in exec_func_with_error_handling
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 591, in code_to_exec
  File "/home/computeruse/computer_use_demo/streamlit.py", line 518, in <module>
    asyncio.run(main())
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/computeruse/computer_use_demo/streamlit.py", line 308, in main
    st.session_state.messages = await sampling_loop(
                                ^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/computer_use_demo/loop.py", line 471, in sampling_loop
    api_response_callback(None, None, e)
  File "/home/computeruse/computer_use_demo/streamlit.py", line 425, in _api_response_callback
    _render_error(error)
  File "/home/computeruse/computer_use_demo/streamlit.py", line 473, in _render_error
    st.error(f"**{error.__class__.__name__}**\n\n{body}", icon=":material/error:")
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/runtime/metrics_util.py", line 410, in wrapped_func
    # Set the execution time to the measured value
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/elements/alert.py", line 75, in error
    single character instead. E.g. "🚨", "🔥", "🤖", etc.
                   ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/string_util.py", line 63, in validate_icon_or_emoji
    re_match = re.search(EMOJI_EXTRACTION_REGEX, text)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/string_util.py", line 108, in validate_material_icon
    """Simplifies number into Human readable format, returns str"""
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/string_util.py", line 55, in is_material_icon
    f'The value "{maybe_emoji}" is not a valid emoji. Shortcodes are not allowed, please use a single character instead.'
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'streamlit.material_icon_names'



