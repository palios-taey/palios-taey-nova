## Claude DC Error Log - 2025-04-18

### API Error
```
BadRequestError

Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'beta: Extra inputs are not permitted'}}

Traceback:

File "/home/computeruse/computer_use_demo/loop.py", line 213, in sampling_loop
    stream = client.beta.messages.create(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_utils/_utils.py", line 275, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/resources/beta/messages/messages.py", line 958, in create
    return self._post(
           ^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1330, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1007, in request
    return self._request(
           ^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1111, in _request
    raise self._make_status_error_from_response(err.response) from None

anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'beta: Extra inputs are not permitted'}}
```

### Module Import Error
```
Setup complete!
You may need to refresh the browser to see the changes.
Starting model: claude-3-7-sonnet-20250219...
Running in local mode (CLAUDE_ENV=dev)
Starting Claude DC Streamlit application...
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/computeruse/computer_use_demo/streamlit.py", line 21, in <module>
    from computer_use_demo.tools import ToolResult, ToolVersion
  File "/home/computeruse/computer_use_demo/streamlit.py", line 20, in <module>
  from streamlit.delta_generator import DeltaGenerator
ModuleNotFoundError: No module named 'streamlit.delta_generator'
ERROR: Failed to start Streamlit: Command '['python', '-m', 'streamlit', 'run', 'streamlit.py', '--server.address=0.0.0', '--server.port=8501', '--server.enableCORS=false']' returned non-zero exit status 1.
```