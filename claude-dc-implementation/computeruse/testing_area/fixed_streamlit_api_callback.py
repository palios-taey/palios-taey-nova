"""
Fixed implementation of the _render_api_response and _api_response_callback functions
from streamlit.py to prevent the 'NoneType' object has no attribute 'method' error.
"""

import httpx
from typing import Union, Optional
from streamlit.delta_generator import DeltaGenerator

def _api_response_callback(
    request: Union[httpx.Request, None],
    response: Union[httpx.Response, object, None],
    error: Optional[Exception],
    tab: DeltaGenerator,
    response_state: dict,
):
    """
    Handle API response callbacks.
    
    Fixed version that properly handles None values for request and response.
    """
    # Import required modules
    from datetime import datetime
    
    # Generate a unique ID for this response
    response_id = datetime.now().isoformat()
    
    # Store the request and response, even if they are None
    response_state[response_id] = (request, response)
    
    # Handle any errors
    if error:
        _render_error(error)
        
    # Render the API response in the logs tab
    _render_api_response(request, response, response_id, tab)

def _render_api_response(
    request: Union[httpx.Request, None],
    response: Union[httpx.Response, object, None],
    response_id: str,
    tab: DeltaGenerator,
):
    """
    Render API request/response in the logs tab.
    
    Fixed version that properly handles None values for request and response.
    """
    with tab:
        with tab.expander(f"Request/Response ({response_id})"):
            newline = "\n\n"
            
            # Request details - properly handle None
            if request is not None:
                # Safe access to attributes
                method = getattr(request, 'method', 'Unknown')
                url = getattr(request, 'url', 'Unknown')
                headers = getattr(request, 'headers', {})
                
                tab.markdown(
                    f"`{method} {url}`{newline}{newline.join(f'`{k}: {v}`' for k, v in headers.items())}"
                )
                try:
                    # Only try to read and decode if request has read method
                    if hasattr(request, 'read'):
                        body = request.read().decode()
                        tab.json(body)
                    else:
                        tab.text("Could not decode request body - no read method")
                except Exception as e:
                    tab.text(f"Could not decode request body: {str(e)}")
            else:
                tab.markdown("*No request data available*")
                    
            tab.markdown("---")
            
            # Response details - properly handle None
            if response is not None:
                if isinstance(response, httpx.Response):
                    # Handle httpx.Response
                    tab.markdown(
                        f"`{response.status_code}`{newline}{newline.join(f'`{k}: {v}`' for k, v in response.headers.items())}"
                    )
                    try:
                        tab.json(response.text)
                    except Exception:
                        tab.text(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
                else:
                    # Handle other response types
                    tab.write(response)
            else:
                tab.markdown("*No response data available*")