2025-04-30 01:28:52,262 - INFO - Starting streaming request to claude-3-7-sonnet-20250219
2025-04-30 01:29:53,089 - INFO - HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
2025-04-30 01:29:53,095 - INFO - Message started
2025-04-30 01:29:53,095 - INFO - Content block started: thinking
2025-04-30 01:29:55,623 - INFO - Content block stopped
2025-04-30 01:29:55,623 - INFO - Content block started: text
2025-04-30 01:29:56,862 - INFO - Content block stopped
2025-04-30 01:29:56,862 - INFO - Content block started: tool_use
2025-04-30 01:29:57,494 - INFO - Content block stopped
2025-04-30 01:29:57,494 - INFO - Received tool use: {"command": "view", "path": "/home/computeruse/computer_use_demo"}
2025-04-30 01:29:57,497 - INFO - Executing tool with type: , name: 
2025-04-30 01:29:57,497 - ERROR - Error in streaming: 'Delta' object has no attribute 'thinking'
2025-04-30 01:29:57,497 - ERROR - Error in sampling loop: 'Delta' object has no attribute 'thinking'
2025-04-30 01:29:57.501 Uncaught app execution
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
  File "/home/computeruse/computer_use_demo/loop.py", line 437, in sampling_loop
    response = await agent_loop(
               ^^^^^^^^^^^^^^^^^
  File "/home/computeruse/computer_use_demo/loop.py", line 270, in agent_loop
    if event.delta.thinking:
       ^^^^^^^^^^^^^^^^^^^^
  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/pydantic/main.py", line 891, in __getattr__
AttributeError: 'Delta' object has no attribute 'thinking'



