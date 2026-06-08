import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Configuration - points to your FastAPI service port
API_URL = "http://127.0.0.1:30237" 

st.set_page_config(page_title="NLP Document Intelligence", page_icon="📄", layout="wide")

st.title("📄 NLP Document Intelligence Platform")
st.markdown("---")

# Sidebar for Uploads
st.sidebar.header("📥 Ingestion Panel")
uploaded_file = st.sidebar.file_uploader("Choose a document", type=["txt", "pdf", "docx"])

if st.sidebar.button("Upload & Process"):
    if uploaded_file is not None:
        with st.spinner("Processing document through NLP Pipeline..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(f"{API_URL}/upload/", files=files)
                if response.status_code == 200:
                    st.sidebar.success(f"Success: {uploaded_file.name} processed!")
                    st.rerun()
                else:
                    st.sidebar.error(f"Error: {response.text}")
            except Exception as e:
                st.sidebar.error(f"Could not connect to backend: {e}")
    else:
        st.sidebar.warning("Please select a file first.")

# Main Dashboard Layout
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📚 Processed Documents Summary")
    
    # Fetch processed data from database via FastAPI endpoint
    try:
        res = requests.get(f"{API_URL}/documents/")
        if res.status_code == 200 and res.json():
            docs_data = res.json()
            df = pd.DataFrame(docs_data)
            
            # Selection box to view full summary
            selected_doc = st.selectbox("Select a document to inspect details:", df['filename'].unique())
            doc_details = df[df['filename'] == selected_doc].iloc[0]
            
            st.markdown(f"### 📋 Summary for **{selected_doc}**")
            st.info(doc_details['summary'])
            
            # Text Enhancements / Metadata Display
            st.markdown("### ✨ Document Insights & Enhancements")
            metrics_col1, metrics_col2 = st.columns(2)
            metrics_col1.metric("Word Count", doc_details.get('word_count', 'Calculating...'))
            metrics_col2.metric("Processing Status", "COMPLETED", delta="Ready")
            
        else:
            st.info("No processed documents found in PostgreSQL. Upload a file on the sidebar to begin!")
    except Exception as e:
        st.error(f"Unable to fetch database records from API: {e}")

with col2:
    st.subheader("📊 Document Analytics")
    if 'df' in locals() and not df.empty:
        # Simple Visualization of Word Counts across files
        st.markdown("#### Text Length Comparison")
        fig, ax = plt.subplots()
        ax.bar(df['filename'], df.get('word_count', [len(s.split()) for s in df['summary']]), color='#4682B4')
        plt.xticks(rotation=45, ha='right')
        ax.set_ylabel("Words")
        st.pyplot(fig)
    else:
        st.write("Analytics visualization will render once documents are active.")