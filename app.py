import streamlit as st
from scrape import get_tables, download_files
import requests

def set_page_config():
    """
    Sets the page configuration.
    """
    st.set_page_config(
        page_title="Download Planning Files"
        # layout="wide"
    )

    if "df" not in st.session_state:
        st.session_state.df = None
    
    if "links_with_text" not in st.session_state:
        st.session_state.links_with_text = None
    
    if "show_table" not in st.session_state:
        st.session_state.show_table = True
    
    if "download_complete" not in st.session_state:
        st.session_state.download_complete = False

    if "download_progress" not in st.session_state:
        st.session_state.download_progress = 0

def start_download(links_with_text, url):
    st.session_state.show_table = False
    download_files(links_with_text, url)
    st.session_state.download_complete = True

#-------------------------------------------------#
# Page layout

set_page_config()

st.title("Download Planning Files")
ip = requests.get('https://curlmyip.org/').text
st.write(ip)

url = st.text_input("URL", key="url")

if url and st.session_state.download_complete == False:
    st.session_state.df, st.session_state.links_with_text = get_tables(url)
    if st.session_state.df is None:
        st.write("No table found...")
    else:     
        st.button("Start Download", key="scrape", on_click=start_download,args=[st.session_state.links_with_text, url])
        with st.expander("Show table", expanded=st.session_state.show_table):
            st.write(st.session_state.df)
        with st.expander("Show links", expanded=st.session_state.show_table):
            for link in st.session_state.links_with_text:
                st.write(link)
    

if st.session_state.download_complete:
    st.balloons()
    folder_name = 'downloaded_files'
    zip_name = folder_name + '.zip'
    st.download_button(
        label="Download Zipped Files",
        data=open(zip_name, 'rb').read(),
        file_name=zip_name,
        mime="application/zip"
    )
