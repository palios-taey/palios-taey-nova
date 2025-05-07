import streamlit as st

st.title("Basic Streamlit Test")
st.write("If you can see this, Streamlit is working at the basic level!")

if st.button("Click me"):
    st.success("Button clicked!")
