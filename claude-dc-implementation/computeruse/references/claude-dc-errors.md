Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Too much media: 0 document pages + 101 images > 100'}}

Traceback:

File "/home/computeruse/computer_use_demo/loop.py", line 139, in sampling_loop
    raw_response = client.beta.messages.with_raw_response.create(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_legacy_response.py", line 387, in wrapped
    return cast(LegacyAPIResponse[R], func(*args, **kwargs))
                                      ^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_utils/_utils.py", line 283, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/resources/beta/messages/messages.py", line 952, in create
    return self._post(
           ^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1279, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/home/computeruse/.pyenv/versions/3.11.6/lib/python3.11/site-packages/anthropic/_base_client.py", line 1074, in request
    raise self._make_status_error_from_response(err.response) from None

anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Too much media: 0 document pages + 101 images > 100'}}
