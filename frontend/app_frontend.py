import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://nlp-fastapi-service.default.svc.cluster.local:80"

st.set_page_config(
    page_title="NLP Document Intelligence", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4A90E2;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-completed { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .status-active { background-color: #cce5ff; color: #004085; border: 1px solid #b8daff;}
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #4A90E2;
    }
    </style>
""", unsafe_allow_html=True)


st.markdown('<p class="main-header">🧠 NLP Document Intelligence Platform</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated Ingestion, OCR, and AI Summarization Pipeline via Kubernetes</p>', unsafe_allow_html=True)
st.markdown("---")


with st.sidebar:
    st.header("📥 Data Ingestion")
    st.markdown("Drop a file to trigger the distributed processing pipeline.")
    
    uploaded_file = st.file_uploader("Upload Document", type=["txt", "pdf", "docx"], label_visibility="collapsed")

    if st.button("🚀 Upload & Process", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner("Uploading to FastAPI & queueing job..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                try:
                    response = requests.post(f"{API_URL}/upload/", files=files)
                    if response.status_code in [200, 202]:
                        st.toast(f"🎉 Pipeline triggered for {uploaded_file.name}!", icon="✅")
                        st.success("Sent to Distributed Queue")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Backend API Unreachable: {e}")
        else:
            st.warning("⚠️ Please select a file first.")
            
    st.markdown("---")
    st.header("🔄 Pipeline State")
    if st.button("Refresh Dashboard", use_container_width=True):
        st.rerun()

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
    st.error(f"Database sync failed. Is the API running? Error: {e}")

# Main Dashboard Layout
if not df.empty:
    # Search and Filter Bar
    search_query = st.text_input("🔍 Search documents by name or keyword...", "", placeholder="e.g., invoice, financial report...")
    
    if search_query:
        filtered_df = df[
            df['filename'].str.contains(search_query, case=False, na=False) | 
            df['summary'].str.contains(search_query, case=False, na=False)
        ]
    else:
        filtered_df = df

    if not filtered_df.empty:
       
        selected_doc = st.selectbox("Select a document to inspect cognitive insights:", filtered_df['filename'].unique())
        doc_details = filtered_df[filtered_df['filename'] == selected_doc].iloc[0]
        
        doc_status = doc_details.get('status', 'COMPLETED').upper()
        
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selected File", selected_doc[:20] + "..." if len(selected_doc) > 20 else selected_doc)
        m2.metric("Word Count", doc_details.get('word_count', len(str(doc_details.get('extracted_text', '')).split())))
        m3.metric("Storage Node", "MinIO Object Store")
        m4.metric("Pipeline Stage", doc_status, delta="Synced" if doc_status == "COMPLETED" else "Active", delta_color="normal")

        st.markdown("---")
        
        # Side-by-Side Split-Screen Analysis
        st.subheader("✨ Cognitive Deep-Dive")
        view_col1, view_col2 = st.columns(2)
        
        with view_col1:
            st.markdown("##### 📄 Extracted Ground Truth")
            raw_text = doc_details.get('extracted_text', doc_details.get('raw_text', "Raw source text tracking not enabled."))
            st.text_area(label="Source Content", value=raw_text, height=400, disabled=True, label_visibility="collapsed")
            
        with view_col2:
            st.markdown("##### 🧠 Hugging Face Executive Summary")
            st.text_area(label="Summary Content", value=doc_details['summary'], height=400, disabled=True, label_visibility="collapsed")
            
        # Document Analytics Row
        st.markdown("---")
        st.subheader("📊 Corpus Analytics")
        fig, ax = plt.subplots(figsize=(10, 2.5))
        
        words_list = []
        for index, row in filtered_df.iterrows():
            w_count = row.get('word_count')
            if not w_count or pd.isna(w_count):
                w_count = len(str(row.get('summary', '')).split())
            words_list.append(w_count)
            
        ax.bar(filtered_df['filename'].str[:15], words_list, color='#4A90E2', alpha=0.8, edgecolor='none')
        
        # Clean up chart UI
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.xticks(rotation=0)
        ax.set_ylabel("Extracted Words", color='#6c757d')
        fig.patch.set_facecolor('none')
        ax.set_facecolor('none')
        
        st.pyplot(fig)
        
    else:
        st.info("No documents match your search criteria.")
else:
    # 🌟 PRO-TIP FOR LINKEDIN: Show Architecture when empty!
    st.info("💡 Awaiting document ingestion. System is fully armed and ready.")
    
    st.markdown("### 🏗️ Live Cluster Architecture")
    st.markdown("""
    This platform operates on a distributed microservices architecture deployed via GitOps (Argo CD) on Kubernetes.
    
    * **Frontend:** Streamlit Edge UI
    * **API Gateway:** FastAPI with asynchronous streaming
    * **Message Broker:** Redis Message Queue for job distribution
    * **Storage:** MinIO (S3-compatible) Object Storage for binary blobs
    * **AI Workers:** Scalable Python Celery workers leveraging Hugging Face Transformers (`distilbart-cnn`)
    * **Database:** PostgreSQL for persistent telemetry and summary indexing
    """)
    
    st.markdown("---")
    st.caption("Engineered for Scalable Document Intelligence")
