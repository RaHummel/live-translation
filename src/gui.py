import streamlit as st

# Set page title and layout
st.set_page_config(page_title="Live Translation App", page_icon=":earth_americas:", layout="wide")

# Sidebar for navigation
sidebar = st.sidebar
sidebar.image("./img/live-translation.png", use_container_width=True)

# Tabs as sidebar menu
tabs = sidebar.radio("Choose an option", ["Translation", "Input Settings", "Translation Settings", "Output Settings"])

# Main page - Translation with Start/Stop buttons and output
if tabs == "Translation":
    st.header("Translation")

    # Start and Stop buttons
    col1, col2 = st.columns(2)
    with col1:
        start_translation = st.button("Start",icon=":material/play_circle:", use_container_width=True)
    with col2:
        stop_translation = st.button("Stop",icon=":material/stop_circle:", use_container_width=True)

    # Status indicator
    if start_translation:
        st.success("Translation in progress...")
    elif stop_translation:
        st.error("Translation stopped.")
    else:
        st.info("Ready for translation.")

    # Show transcription and translation checkboxes
    show_transcription = st.checkbox("Show Transcription")
    show_translation = st.checkbox("Show Translated Text")

    # Transcription text area (only visible if show_transcription is checked)
    if show_transcription:
        st.subheader("Transcription")
        transcribed_text = st.text_area("Transcribed Text", height=150)

    # Translation text area (only visible if show_translation is checked)
    if show_translation:
        st.subheader("Translation")
        translated_text = st.text_area("Translated Text", height=150)

# Input Settings
elif tabs == "Input Settings":
    st.header("Input Settings")

    # Select input language
    input_language = st.selectbox("Input Language", ["German", "English", "French"])

    # Select input device
    input_device = st.selectbox("Input Device", ["Microphone 1", "Microphone 2"])

    # Select translation provider
    translator = st.selectbox("Translation Provider", ["AWS", "Google Translate"])
    api_key = st.text_input(f"{translator} API Key", type="password")

# Translation Settings
elif tabs == "Translation Settings":
    st.header("Translation Settings")

    # Select target languages
    st.write("Target Languages:")
    target_languages = ["German", "English", "French", "Spanish"]
    selected_target_languages = [lang for lang in target_languages if st.checkbox(lang, key=lang)]

# Output Settings
elif tabs == "Output Settings":
    st.header("Output Settings")

    # Choose output option
    output_option = st.radio("Output Option", ["Speaker", "Mumble"])

    if output_option == "Speaker":
        # Select output language if Speaker is chosen
        output_language = st.selectbox("Output Language", target_languages)
    elif output_option == "Mumble":
        # Mumble configuration if Mumble is chosen
        st.subheader("Mumble Configuration")
        server_endpoint = st.text_input("Server Endpoint")
        channel_structure = st.text_area("Channel Structure for Target Languages")
        start_own_server = st.checkbox("Start Own Mumble Server")

        if start_own_server:
            # Configuration for own Mumble server
            server_name = st.text_input("Server Name")
            superuser_password = st.text_input("SuperUser Password", type="password")
