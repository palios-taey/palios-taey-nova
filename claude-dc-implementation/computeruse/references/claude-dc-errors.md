2025-04-29 23:25:50,075 - INFO - Starting streaming request to claude-3-7-sonnet-20250219
2025-04-29 23:26:29,689 - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 400 Bad Request"
2025-04-29 23:26:29,689 - ERROR - Error in streaming: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'tools.1.bash_20250124.name: Field required'}}
2025-04-29 23:26:29,689 - ERROR - Error in sampling loop: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'tools.1.bash_20250124.name: Field required'}}
2025-04-29 23:26:29.693 Uncaught app execution
Traceback (most recent call last):
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 121, in exec_func_with_error_handling
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 591, in code_to_exec
  File "/home/computeruse/computer_use_demo/streamlit.py", line 636, in <module>
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
  File "/home/computeruse/computer_use_demo/streamlit.py", line 369, in main
    st.session_state.messages = await sampling_loop(
                                ^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/computer_use_demo/loop.py", line 458, in sampling_loop
    response = await agent_loop(
               ^^^^^^^^^^^^^^^^^
  File "/home/computeruse/computer_use_demo/loop.py", line 216, in agent_loop
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
anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'tools.1.bash_20250124.name: Field required'}}



