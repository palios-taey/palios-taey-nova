async def sampling_loop(
    # Existing args...
    stream: bool = True,  # Enable streaming by default
):
    # Existing setup code...

    try:
        if stream:
            # Streaming response
            with client.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=system.text,
                tools=tool_collection.to_params(),
                betas=betas,
                **(extra_body or {}),
                stream=True,
            ) as response_stream:
                response_blocks = []
                for event in response_stream:
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "text":
                            response_blocks.append(BetaTextBlockParam(type="text", text=""))
                        elif block.type == "tool_use":
                            response_blocks.append(cast(BetaToolUseBlockParam, block.model_dump()))
                        elif block.type == "thinking":
                            response_blocks.append({"type": "thinking", "thinking": ""})
                        # Add other types as needed
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            response_blocks[-1]["text"] += event.delta.text
                        elif event.delta.type == "thinking_delta":
                            response_blocks[-1]["thinking"] += event.delta.text
                    elif event.type == "message_stop":
                        api_response_callback(None, {"status_code": 200, "headers": response_stream.get_raw_response().headers}, None)
                # Process blocks as before
        else:
            # Non-streaming response
            response = client.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=system.text,
                tools=tool_collection.to_params(),
                betas=betas,
                **(extra_body or {}),
                stream=False,
            )
            api_response_callback(None, response, None)
            response_blocks = []
            for block in response.content:
                if block.type == "text":
                    response_blocks.append(BetaTextBlockParam(type="text", text=block.text))
                elif block.type == "tool_use":
                    response_blocks.append(cast(BetaToolUseBlockParam, block.model_dump()))
                elif block.type == "thinking":
                    response_blocks.append({"type": "thinking", "thinking": block.thinking})
                elif block.type == "redacted_thinking":
                    response_blocks.append({"type": "redacted_thinking", "data": block.data})
                else:
                    logger.warning(f"Unknown block type: {block.type}")

        # Existing block processing...
    except Exception as e:
        api_response_callback(None, None, e)
        return messages
