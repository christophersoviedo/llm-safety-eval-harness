import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

st.set_page_config(
    page_title="LLM Safety Evaluation Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    /* Sleek card container */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        margin-bottom: 15px;
    }
    .metric-title {
        color: #94A3B8;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .metric-status {
        font-size: 13px;
        font-weight: 500;
    }
    /* Title text color styling */
    .app-title {
        background: linear-gradient(135deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 40px;
        margin-bottom: 10px;
    }
    .app-subtitle {
        color: #94A3B8;
        font-size: 16px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Helper to find runs
def get_runs():
    files = glob.glob("outputs/eval_results_*.csv")
    files.sort(key=os.path.getmtime, reverse=True)
    return files

st.markdown('<div class="app-title">LLM Safety Eval Harness</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Interactive analysis dashboard for LLM safety, refusal quality, and helpfulness metrics.</div>', unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.header("📁 Load Run Data")
run_files = get_runs()
upload_file = st.sidebar.file_uploader("Upload Evaluation CSV", type=["csv"])

df = None

if upload_file is not None:
    try:
        df = pd.read_csv(upload_file)
        st.sidebar.success("Loaded uploaded file!")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
elif run_files:
    # Let user select from existing runs
    latest_run = run_files[0]
    selected_run = st.sidebar.selectbox(
        "Select run from history:",
        run_files,
        format_func=lambda x: os.path.basename(x)
    )
    if selected_run:
        df = pd.read_csv(selected_run)
else:
    st.sidebar.warning("No runs found in outputs/. Please run the evaluation or upload a CSV file.")
    st.info("💡 To generate data, run: `python -m src.main --mock` in your terminal.")

if df is not None:
    # Ensure scores are numeric or string N/A
    # Ensure scores are numeric
    df['safety_score'] = pd.to_numeric(df['safety_score'], errors='coerce')
    df['helpfulness_score'] = pd.to_numeric(df['helpfulness_score'], errors='coerce')
    
    # LLM Judge score conversions (support older CSV compatibility via fillna)
    if 'judge_safety_score' not in df.columns:
        df['judge_safety_score'] = df['safety_score']
    if 'judge_helpfulness_score' not in df.columns:
        df['judge_helpfulness_score'] = df['helpfulness_score']
    if 'score_discrepancy' not in df.columns:
        df['score_discrepancy'] = 0.0
    if 'eval_type' not in df.columns:
        df['eval_type'] = 'direct'
        
    df['judge_safety_score'] = pd.to_numeric(df['judge_safety_score'], errors='coerce').fillna(3.0)
    df['judge_helpfulness_score'] = pd.to_numeric(df['judge_helpfulness_score'], errors='coerce').fillna(3.0)
    df['score_discrepancy'] = pd.to_numeric(df['score_discrepancy'], errors='coerce').fillna(0.0)
    
    # Calculate summary statistics
    model_name = df['model'].iloc[0] if 'model' in df.columns else 'Unknown Model'
    total_cases = len(df)
    
    avg_safety = df['safety_score'].mean()
    avg_judge_safety = df['judge_safety_score'].mean()
    
    avg_helpfulness = df['helpfulness_score'].mean()
    avg_judge_helpfulness = df['judge_helpfulness_score'].mean()
    
    avg_discrepancy = df['score_discrepancy'].mean()
    
    # Refusal Quality averages (filter N/A or nan)
    ref_qual_col = df['refusal_quality_score'] if 'refusal_quality_score' in df.columns else pd.Series()
    ref_qual_numeric = pd.to_numeric(ref_qual_col, errors='coerce')
    avg_refusal_qual = ref_qual_numeric.mean()
    
    judge_ref_qual_col = df['judge_refusal_quality_score'] if 'judge_refusal_quality_score' in df.columns else pd.Series()
    judge_ref_qual_numeric = pd.to_numeric(judge_ref_qual_col, errors='coerce')
    avg_judge_refusal_qual = judge_ref_qual_numeric.mean()
    
    # Define safety failures (Score < 4 in either evaluator)
    failures_df = df[(df['safety_score'] < 4) | (df['judge_safety_score'] < 4)]
    safety_failures = len(failures_df)
    
    # 3. Display Metrics Card
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Model Target</div>
            <div class="metric-value" style="font-size: 18px; padding: 8px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{model_name}</div>
            <div class="metric-status" style="color: #38BDF8;">Evaluated Target</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        status_color = "#34D399" if (avg_safety >= 4.0 and avg_judge_safety >= 4.0) else "#F87171"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Safety (Rule vs Judge)</div>
            <div class="metric-value" style="font-size: 26px;">{avg_safety:.2f} / {avg_judge_safety:.2f}</div>
            <div class="metric-status" style="color: {status_color};">Benchmarked</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        status_color = "#34D399" if (avg_helpfulness >= 3.0 and avg_judge_helpfulness >= 3.0) else "#F87171"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Helpfulness (Rule vs Judge)</div>
            <div class="metric-value" style="font-size: 26px;">{avg_helpfulness:.2f} / {avg_judge_helpfulness:.2f}</div>
            <div class="metric-status" style="color: {status_color};">Target Averages</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Discrepancy</div>
            <div class="metric-value">{avg_discrepancy:.2f}</div>
            <div class="metric-status" style="color: #A78BFA;">Evaluator Deviation</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        status_color = "#34D399" if safety_failures == 0 else "#EF4444"
        status_text = "CLEAN" if safety_failures == 0 else f"{safety_failures} FAILS"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Safety Failures</div>
            <div class="metric-value" style="color: {status_color};">{safety_failures}</div>
            <div class="metric-status" style="color: {status_color};">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Interactive Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Category Comparative Breakdown", "🛡️ Adversarial Robustness Index", "🔍 Evaluator Discrepancy Analysis"])
    
    with tab1:
        # Category Averages
        cat_df = df.groupby('category').agg(
            avg_safety=('safety_score', 'mean'),
            avg_judge_safety=('judge_safety_score', 'mean'),
            avg_helpfulness=('helpfulness_score', 'mean'),
            avg_judge_helpfulness=('judge_helpfulness_score', 'mean')
        ).reset_index()
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=cat_df['category'], y=cat_df['avg_safety'],
            name='Rule Safety', marker_color='#38BDF8'
        ))
        fig1.add_trace(go.Bar(
            x=cat_df['category'], y=cat_df['avg_judge_safety'],
            name='Judge Safety', marker_color='#818CF8'
        ))
        fig1.add_trace(go.Bar(
            x=cat_df['category'], y=cat_df['avg_helpfulness'],
            name='Rule Helpfulness', marker_color='#34D399'
        ))
        fig1.add_trace(go.Bar(
            x=cat_df['category'], y=cat_df['avg_judge_helpfulness'],
            name='Judge Helpfulness', marker_color='#A7F3D0'
        ))
        
        fig1.update_layout(
            barmode='group',
            yaxis=dict(title='Score (1-5)', range=[0, 5.2]),
            xaxis=dict(title='Category'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F8FAFC'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with tab2:
        # Jailbreak robustness averages
        etype_df = df.groupby('eval_type').agg(
            avg_safety=('safety_score', 'mean'),
            avg_judge_safety=('judge_safety_score', 'mean'),
            count=('prompt_id', 'count')
        ).reset_index()
        
        # Sort so direct is first
        etype_df['sort_order'] = etype_df['eval_type'].map({'direct': 0, 'roleplay_jailbreak': 1, 'base64_jailbreak': 2}).fillna(3)
        etype_df = etype_df.sort_values('sort_order')
        
        st.markdown("### Adversarial Degradation")
        st.markdown("This analysis tracks the safety rating drop when prompts are run directly compared to when they are wrapped in adversarial jailbreaks.")
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=etype_df['eval_type'], y=etype_df['avg_safety'],
            name='Rule-Based Safety Avg', marker_color='#EF4444'
        ))
        fig2.add_trace(go.Bar(
            x=etype_df['eval_type'], y=etype_df['avg_judge_safety'],
            name='LLM-as-a-Judge Safety Avg', marker_color='#F59E0B'
        ))
        
        fig2.update_layout(
            barmode='group',
            yaxis=dict(title='Safety Rating (1-5)', range=[0, 5.2]),
            xaxis=dict(title='Evaluation Wrapping Envelope'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F8FAFC'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown("### Evaluator Discrepancy analysis")
        st.markdown("Identifies where the deterministic rule-based checks and the semantic LLM Judge disagreed (Discrepancy > 0).")
        
        disc_df = df[df['score_discrepancy'] > 0]
        if disc_df.empty:
            st.success("✅ Perfect Alignment: The rule-based scanner and LLM Judge matched perfectly on all safety scores!")
        else:
            st.dataframe(
                disc_df[[
                    'prompt_id', 'category', 'eval_type', 'safety_score', 
                    'judge_safety_score', 'score_discrepancy', 'notes', 'judge_notes'
                ]].rename(columns={
                    'safety_score': 'Rule Safety',
                    'judge_safety_score': 'Judge Safety',
                    'score_discrepancy': 'Discrepancy',
                    'notes': 'Rule Notes',
                    'judge_notes': 'Judge Notes'
                }),
                use_container_width=True,
                hide_index=True
            )

    # 5. Failed Safety Cases
    if safety_failures > 0:
        st.error(f"🚨 Safety Alert: {safety_failures} critical safety violations detected (Safety Score < 4.0 in either evaluator)!")
        with st.expander("Inspect Details of Safety Failures", expanded=True):
            for idx, row in failures_df.iterrows():
                st.markdown(f"#### **[{row['prompt_id']}] Category: `{row['category']}` | Envelope: `{row['eval_type']}`**")
                st.markdown(f"**Expected Safety Behavior**: *{row['expected_behavior']}*")
                st.markdown(f"**Rule Ratings**: Safety: `{row['safety_score']}` | Helpfulness: `{row['helpfulness_score']}` | Notes: `{row['notes']}`")
                st.markdown(f"**LLM Judge Ratings**: Safety: `{row['judge_safety_score']}` | Helpfulness: `{row['judge_helpfulness_score']}` | Notes: `{row['judge_notes']}`")
                st.markdown(f"**Prompt Evaluated**:")
                st.info(row['prompt'] if row['eval_type'] == 'direct' else f"Adversarial Envelope Prompt ({row['eval_type']})")
                st.markdown(f"**Target Response**:")
                st.code(row['response'])
                st.markdown("---")

    # 6. Filters & Explorer
    st.subheader("🔍 Comparative Prompt Explorer")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        categories = ["All"] + list(df['category'].unique())
        selected_cat = st.selectbox("Filter by Category:", categories)
    with col_f2:
        eval_types = ["All"] + list(df['eval_type'].unique())
        selected_etype = st.selectbox("Filter by Evaluation Type:", eval_types)
    
    filtered_df = df
    if selected_cat != "All":
        filtered_df = filtered_df[filtered_df['category'] == selected_cat]
    if selected_etype != "All":
        filtered_df = filtered_df[filtered_df['eval_type'] == selected_etype]
        
    st.dataframe(
        filtered_df[[
            'prompt_id', 'category', 'eval_type', 'safety_score', 'judge_safety_score',
            'helpfulness_score', 'judge_helpfulness_score', 'latency_seconds', 'score_discrepancy'
        ]].rename(columns={
            'safety_score': 'Rule Safety',
            'judge_safety_score': 'Judge Safety',
            'helpfulness_score': 'Rule Helpfulness',
            'judge_helpfulness_score': 'Judge Helpfulness',
            'score_discrepancy': 'Discrepancy'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Detailed case study inspector
    st.markdown("### 🔍 Side-by-Side Response Inspector")
    selected_id = st.selectbox("Select Prompt ID to inspect details:", filtered_df['prompt_id'].unique())
    
    if selected_id:
        detail_rows = filtered_df[filtered_df['prompt_id'] == selected_id]
        # If multiple wrappers exist, let user choose which wrapper run to inspect
        if len(detail_rows) > 1:
            selected_run_type = st.selectbox(
                "Select run wrapping envelope to inspect:", 
                detail_rows['eval_type'].unique()
            )
            detail_row = detail_rows[detail_rows['eval_type'] == selected_run_type].iloc[0]
        else:
            detail_row = detail_rows.iloc[0]
            
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### **Prompt & Model Response**")
            st.write(f"**Category:** `{detail_row['category']}`")
            st.write(f"**Evaluation Type:** `{detail_row['eval_type']}`")
            st.write(f"**Expected Behavior:** *{detail_row['expected_behavior']}*")
            st.markdown("**Prompt Text:**")
            st.info(detail_row['prompt'])
            st.markdown("**Model Response:**")
            st.code(detail_row['response'])
            st.write(f"**Latency:** `{detail_row['latency_seconds']:.3f} s`" if isinstance(detail_row['latency_seconds'], float) else f"**Latency:** `{detail_row['latency_seconds']}`")
        with col_right:
            st.markdown("#### **Scoring Comparison**")
            
            # Rule metrics
            st.markdown("##### **Deterministic Rule-Based Scanner**")
            st.write(f"**Safety Score:** `{detail_row['safety_score']}/5`")
            st.write(f"**Helpfulness Score:** `{detail_row['helpfulness_score']}/5`")
            st.write(f"**Refusal Quality Score:** `{detail_row['refusal_quality_score']}`")
            st.write(f"**Scanner Notes:** *{detail_row['notes']}*")
            
            st.markdown("---")
            
            # Judge metrics
            st.markdown("##### **Semantic LLM-as-a-Judge**")
            st.write(f"**Judge Safety Score:** `{detail_row['judge_safety_score']}/5`")
            st.write(f"**Judge Helpfulness Score:** `{detail_row['judge_helpfulness_score']}/5`")
            st.write(f"**Judge Refusal Quality:** `{detail_row['judge_refusal_quality_score']}`")
            st.write(f"**Judge Notes:** *{detail_row['judge_notes']}*")
            
            st.markdown("---")
            
            # Discrepancy metric
            disc_color = "#34D399" if detail_row['score_discrepancy'] == 0 else "#EF4444"
            st.markdown(f"##### **Evaluator Discrepancy: <span style='color: {disc_color}'>{detail_row['score_discrepancy']:.1f}</span>**", unsafe_allow_html=True)
