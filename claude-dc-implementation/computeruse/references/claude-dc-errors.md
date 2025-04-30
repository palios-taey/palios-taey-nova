2025-04-30 02:11:25.266 Uncaught app execution
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
  File "/home/computeruse/computer_use_demo/streamlit.py", line 318, in main
    _render_message(
  File "/home/computeruse/computer_use_demo/streamlit.py", line 627, in _render_message
    st.code(f'Tool Use: {message["name"]}\nInput: {message["input"]}')
                         ~~~~~~~^^^^^^^^
KeyError: 'name'


