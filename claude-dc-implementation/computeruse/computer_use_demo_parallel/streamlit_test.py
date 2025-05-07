"""
Simple Streamlit test script.
"""

import streamlit as st

st.title("Streamlit Test")
st.write("If you can see this, Streamlit is working correctly!")

# Add a simple counter
if "count" not in st.session_state:
    st.session_state.count = 0

if st.button("Increment Counter"):
    st.session_state.count += 1

st.write(f"Counter: {st.session_state.count}")