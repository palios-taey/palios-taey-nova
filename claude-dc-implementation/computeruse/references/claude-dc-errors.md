2025-04-29 21:04:47.219 Uncaught app execution
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

