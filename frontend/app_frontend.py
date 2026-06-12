import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# CORRECTED: Point to the internal Kubernetes service name & container port
API_URL = "http://nlp-fastapi-service:8000" 

st.set_page_config(page_title="NLP Document Intelligence", page_icon="📄", layout="wide")

# Custom CSS for polished layout and progress tags
st.markdown("""
    <style>
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .status-completed { background-color: #d4edda; color: #155724; }
    .status-processing { background-color: #fff3cd; color: #856404; }
    .status-pending { background-color: #e2e3e5; color: #383d41; }
    </style>
""", unsafe_allow_html=True)

st.title("📄 NLP Document Intelligence Platform")
st.markdown("---")

# Sidebar for Uploads
st.sidebar.header("📥 Ingestion Panel")
uploaded_file = st.sidebar.file_uploader("Choose a document", type=["txt", "pdf", "docx"])

if st.sidebar.button("Upload & Process"):
    if uploaded_file is not None:
        with st.spinner("Uploading to FastAPI & queueing job..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(f"{API_URL}/upload/", files=files)
                if response.status_code == 200 or response.status_code == 202:
                    st.sidebar.success(f"🎉 Checked in: {uploaded_file.name} sent to pipeline!")
                    st.rerun()
                else:
                    st.sidebar.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.sidebar.error(f"Could not connect to backend API: {e}")
    else:
        st.sidebar.warning("Please select a file first.")

# Fetch processed data from database via FastAPI endpoint
try:
    res = requests.get(f"{API_URL}/documents/")
    if res.status_code == 200:
        docs_data = res.json()
        df = pd.DataFrame(docs_data)
    else:
        df = pd.DataFrame()
        st.error(f"Backend returned an error code: {res.status_code}")
except Exception as e:
    df = pd.DataFrame()
    st.error(f"Unable to fetch database records from API: {e}")

# Main Dashboard Layout
if not df.empty:
    # 🔍 Premium Feature: Search and Filter Bar
    st.subheader("📚 Explore Ingested Documents")
    search_query = st.text_input("🔍 Search documents by name or content...", "")
    
    if search_query:
        # Filter rows that match filename or summary text
        filtered_df = df[
            df['filename'].str.contains(search_query, case=False, na=False) | 
            df['summary'].str.contains(search_query, case=False, na=False)
        ]
    else:
        filtered_df = df

    if not filtered_df.empty:
        # Selection dropdown
        selected_doc = st.selectbox("Select a document to inspect details:", filtered_df['filename'].unique())
        doc_details = filtered_df[filtered_df['filename'] == selected_doc].iloc[0]
        
        # Get dynamic status defaults if not provided explicitly by the backend payload
        doc_status = doc_details.get('status', 'COMPLETED').upper()
        
        # Auto-Refresh Toggle for long runs
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔄 Live Dashboard Controls")
        if st.sidebar.button("Refresh View"):
            st.rerun()

        # Layout splitting: Data Metrics on Top
        m1, m2, m3 = st.columns(3)
        m1.metric("Selected Document", selected_doc[:25] + "..." if len(selected_doc) > 25 else selected_doc)
        m2.metric("Word Count", doc_details.get('word_count', len(str(doc_details.get('extracted_text', '')).split())))
        m3.metric("Pipeline Stage", doc_status, delta="Synced" if doc_status == "COMPLETED" else "Active")

        st.markdown("---")
        
        # 🎨 Premium Feature: Side-by-Side Split-Screen Analysis
        st.subheader("✨ Deep-Dive Cognitive View")
        view_col1, view_col2 = st.columns(2)
        
        with view_col1:
            st.markdown("### 📄 Extracted Raw Ground Truth")
            # Fallback to summary snippet if raw text missing
            raw_text = doc_details.get('extracted_text', doc_details.get('raw_text', "Raw source text tracking not enabled."))
            st.text_area(label="Source Content", value=raw_text, height=350, disabled=True, label_visibility="collapsed")
            
        with view_col2:
            st.markdown("### 🧠 AI Generated Executive Summary")
            st.text_area(label="Summary Content", value=doc_details['summary'], height=350, disabled=True, label_visibility="collapsed")
            
        # 📊 Document Analytics Row
        st.markdown("---")
        st.subheader("📊 Corpus Analytics")
        fig, ax = plt.subplots(figsize=(10, 3))
        
        # Calculate sizing dynamics
        words_list = []
        for index, row in filtered_df.iterrows():
            w_count = row.get('word_count')
            if not w_count or pd.isna(w_count):
                w_count = len(str(row.get('summary', '')).split())
            words_list.append(w_count)
            
        ax.bar(filtered_df['filename'].str[:15], words_list, color='#4682B4')
        plt.xticks(rotation=15, ha='right')
        ax.set_ylabel("Words")
        ax.set_title("Text Metric footprint across active selection cluster")
        st.pyplot(fig)
        
    else:
        st.warning("No documents match your search criteria.")
else:
    st.info("💡 No processed documents found in PostgreSQL. Drop a file into the Ingestion Panel on the left to start the pipeline!")
