def _render_api_response(
    request: httpx.Request,
    response: httpx.Response | object | None,
    response_id: str,
    tab: DeltaGenerator,
):
    with tab:
        with st.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            if request:
                st.markdown(f"`{request.method} {request.url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in request.headers.items())}")
                st.json(request.read().decode())
            else:
                st.text("No request object available")
            st.markdown("---")
            if isinstance(response, httpx.Response):
                st.markdown(f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}")
                st.text(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
            elif hasattr(response, "model_dump"):  # BetaMessage
                st.json(response.model_dump())
            elif isinstance(response, dict):  # Streaming placeholder
                st.markdown(f"`{response.get('status_code', 'N/A')}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.get('headers', {}).items())}")
                st.text("Streaming response processed")
            else:
                st.write(response)

def _render_message(sender: Sender, message: str | BetaContentBlockParam | ToolResult):
    is_tool_result = not isinstance(message, str | dict)
    if not message or (is_tool_result and st.session_state.hide_images and not hasattr(message, "error") and not hasattr(message, "output")):
        return
    with st.chat_message(sender):
        if is_tool_result:
            # Existing tool result handling...
        elif isinstance(message, dict):
            if message["type"] == "text":
                st.write(message.get("text", ""))
            elif message["type"] == "tool_use":
                st.code(f'Tool Use: {message["name"]}\nInput: {message["input"]}')
            elif message["type"] == "thinking":
                st.markdown(f"[Thinking]\n\n{message.get('thinking', '')}")
            elif message["type"] == "redacted_thinking":
                st.markdown("[Redacted Thinking] - Encrypted for safety")
            else:
                st.write(f"Unknown type: {message}")
        else:
            st.markdown(message)
