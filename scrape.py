from bs4 import BeautifulSoup
import requests
import pandas as pd
from io import StringIO  # Add this import at the top
from urllib.parse import urljoin, urlparse
import re
import os
import shutil
import zipfile
import streamlit as st



def extract_tables_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    
    dfs = []
    for table in tables:
        # Wrap the HTML string in StringIO before passing to read_html
        df = pd.read_html(StringIO(str(table)))[0]
        dfs.append(df)

    return dfs, tables

def table_with_most_links(tables, dfs):
    max_links = 0
    table_with_max_links = None
    
    for i, table in enumerate(tables):
        links_count = len(table.find_all('a', href=True))
        if links_count > max_links:
            max_links = links_count
            table_with_max_links = table
            df = dfs[i]
            
    return table_with_max_links, df, max_links

def extract_links_with_row_text(table, base_url):
    """
    Extracts links from the table and associates each link with its corresponding row's text.
    """
    links_with_text = []

    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        row_text = ' '.join(cell.get_text() for cell in cells)
        link = row.find('a', href=True)
        if link:
            href = link['href']
            if not is_absolute_url(href):
                href = urljoin(base_url, href)
            links_with_text.append((href, row_text))

    return links_with_text

def sanitize_filename(filename):
    """
    Keeps only alphanumeric characters and strips out the rest.
    """
    return re.sub(r'[^a-zA-Z0-9]', '_', filename)

def is_absolute_url(url):
    """
    Returns True if the URL is absolute, False otherwise.
    """
    return bool(urlparse(url).netloc)

def download_files_from_links(links_with_text, save_directory, base_url):
    # Ensure the save directory exists
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Mapping of desired file extensions to their MIME types
    file_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'rtf': 'application/rtf'
    }

    num_links = len(links_with_text)

    cookies = requests.get(base_url).cookies
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }


    for link, row_text in links_with_text:
        try:

            response = requests.get(link, headers=headers, cookies=cookies, stream=True)
            content_type = response.headers.get('Content-Type')
            print(f"Downloading: {link} ({content_type})")

            # Check if content type matches any of our desired file types
            for extension, mime in file_types.items():
                if content_type == mime:
                    print(f"Matched MIME type: {mime} for {link}")
                    sanitized_name = sanitize_filename(row_text)
                    file_name = os.path.join(save_directory, sanitized_name + '.' + extension)
                    with open(file_name, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded: {file_name}")
            
                    st.session_state.download_progress += (1 / num_links)
                    break

        except Exception as e:
            print(f"Error downloading {link}. Reason: {e}")

def delete_downloads_and_zip():
    """
    Deletes the 'downloaded_files' directory and its zipped version if they exist.
    """
    folder_name = 'downloaded_files'
    zip_name = folder_name + '.zip'
    
    # Delete the folder if it exists
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
        print(f"Deleted folder: {folder_name}")
    
    # Delete the zip file if it exists
    if os.path.exists(zip_name):
        os.remove(zip_name)
        print(f"Deleted zip file: {zip_name}")

def zip_directory(directory_path, output_filename):
    """
    Zips the specified directory and saves it as output_filename.
    """
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory_path)  # relative path within the zip file
                zipf.write(file_path, arcname)


def get_tables(url):

    df, tables = extract_tables_from_url(url)
    table, df, max_links_count = table_with_most_links(tables, df)
    links_with_text = extract_links_with_row_text(table, url)

    return df, links_with_text


def download_files(links_with_text, base_url):
    
    SAVE_DIRECTORY = './downloaded_files'
    
    delete_downloads_and_zip()
    download_files_from_links(links_with_text, SAVE_DIRECTORY, base_url)
    zip_directory(SAVE_DIRECTORY, SAVE_DIRECTORY + '.zip')
