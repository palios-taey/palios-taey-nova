AttributeError: 'NoneType' object has no attribute 'method'
2025-04-29 22:52:47,493 - INFO - Using Anthropic SDK version: 0.47.0
/home/computeruse/computer_use_demo/loop.py:38: UserWarning: Expected Anthropic SDK v0.50.0, but found v0.47.0. This may cause issues.
  warnings.warn(f"Expected Anthropic SDK v0.50.0, but found v{anthropic_version}. This may cause issues.")
2025-04-29 22:52:48.982 Uncaught app execution
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
  File "/home/computeruse/computer_use_demo/streamlit.py", line 282, in main
    _render_api_response(request, response, identity, http_logs)
  File "/home/computeruse/computer_use_demo/streamlit.py", line 448, in _render_api_response
    f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
        ^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'method'
2025-04-29 22:53:42,109 - INFO - Using Anthropic SDK version: 0.47.0
/home/computeruse/computer_use_demo/loop.py:38: UserWarning: Expected Anthropic SDK v0.50.0, but found v0.47.0. This may cause issues.
  warnings.warn(f"Expected Anthropic SDK v0.50.0, but found v{anthropic_version}. This may cause issues.")
2025-04-29 22:53:42,109 - ERROR - VERSION MISMATCH: Expected Anthropic SDK v0.50.0, found v0.47.0
2025-04-29 22:53:42,109 - ERROR - To fix this issue, run: ./update_anthropic_sdk.sh
2025-04-29 22:53:43.634 Uncaught app execution
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
  File "/home/computeruse/computer_use_demo/streamlit.py", line 282, in main
    _render_api_response(request, response, identity, http_logs)
  File "/home/computeruse/computer_use_demo/streamlit.py", line 448, in _render_api_response
    f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}"
        ^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'method'


