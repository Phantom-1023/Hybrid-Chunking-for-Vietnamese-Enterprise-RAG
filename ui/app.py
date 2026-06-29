import random
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from config.constants import STRATEGY_COLLECTIONS
from config.settings import settings
from src.dataset_loader import DatasetLoadError, load_vietnamese_rag_snapshot
from src.generator import AnswerGenerator
from src.retriever import StrategyRetriever


st.set_page_config(
    page_title="RAG Enterprise Demo",
    layout="wide",
    initial_sidebar_state="expanded",
)

SAMPLE_QUESTIONS = [
    "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?",
    "Minh Tú đã vượt qua thử thách nào trong chương trình?",
    "Kết quả chung cuộc của Minh Tú trong tập này là gì?",
]


@st.cache_resource
def get_retriever():
    return StrategyRetriever()


@st.cache_resource
def get_generator():
    return AnswerGenerator()


@st.cache_data(show_spinner=False)
def load_demo_records():
    snapshot = load_vietnamese_rag_snapshot(
        dataset_name=settings.verify_dataset_name,
        config_name=settings.verify_dataset_config,
        limit=settings.verify_record_limit,
    )
    return [
        {
            "record_id": record.record_id,
            "question": record.question or "",
            "ground_truth": record.ground_truth or "",
            "joined_context": record.joined_context,
        }
        for record in snapshot.selected_records
        if record.question and record.joined_context
    ]


def run_query(question: str, strategy: str, top_k: int):
    chunks = get_retriever().retrieve(question=question, strategy=strategy, top_k=top_k)
    answer = get_generator().generate(question, chunks)
    return answer, chunks


def render_answer(answer: str, chunks, ground_truth: str = ""):
    col_answer, col_truth = st.columns(2) if ground_truth else (None, None)
    if ground_truth:
        with col_answer:
            st.subheader("Generated answer")
            st.write(answer)
        with col_truth:
            st.subheader("Ground truth")
            st.write(ground_truth)
    else:
        st.subheader("Câu trả lời")
        st.write(answer)

    st.subheader("Source chunks")
    for index, chunk in enumerate(chunks, start=1):
        with st.expander(f"Chunk {index} · distance {chunk.distance:.4f}", expanded=index <= 3):
            st.write(chunk.content)
            st.caption("Metadata")
            st.json(chunk.metadata)


with st.sidebar:
    st.header("Cấu hình demo")
    strategy = st.selectbox("Chunking strategy", list(STRATEGY_COLLECTIONS.keys()))
    top_k = st.slider("Top-K chunks", min_value=3, max_value=5, value=5)

st.title("RAG Enterprise Demo - Chunking Strategy Comparison")
st.warning(
    "Demo hiện dùng gemini-embedding-001 do API key hiện tại không hỗ trợ text-embedding-004.",
    icon="⚠️",
)

manual_tab, dataset_tab, benchmark_tab = st.tabs(
    ["Hỏi thủ công", "Demo với dữ liệu thật", "Benchmark evaluation-lite"]
)

with manual_tab:
    sample_question = st.selectbox("Câu hỏi mẫu", SAMPLE_QUESTIONS)
    question = st.text_input("Câu hỏi", value=sample_question)
    ask_clicked = st.button("Hỏi hệ thống", type="primary", key="manual_ask")

    if ask_clicked:
        if not question.strip():
            st.error("Vui lòng nhập câu hỏi.")
        else:
            with st.spinner("Đang truy xuất chunks và sinh câu trả lời..."):
                try:
                    answer, chunks = run_query(question.strip(), strategy, top_k)
                except Exception as exc:
                    st.error(f"Lỗi query: {exc}")
                else:
                    render_answer(answer, chunks)

with dataset_tab:
    st.info("Demo này dùng record ngẫu nhiên từ dataset public, không phải câu hỏi khóa cứng.")

    try:
        records = load_demo_records()
    except DatasetLoadError as exc:
        st.error(f"Không load được dataset: {exc}")
        records = []

    if records:
        if "demo_record_index" not in st.session_state:
            st.session_state.demo_record_index = 0

        left, right = st.columns([0.7, 0.3])
        with left:
            selected_index = st.selectbox(
                "Chọn record trong 50-record subset",
                options=list(range(len(records))),
                index=st.session_state.demo_record_index,
                format_func=lambda index: f"Record {records[index]['record_id']} · {records[index]['question'][:80]}",
            )
            st.session_state.demo_record_index = selected_index
        with right:
            if st.button("Random record", use_container_width=True):
                st.session_state.demo_record_index = random.randrange(len(records))
                st.rerun()

        record = records[st.session_state.demo_record_index]
        st.write(f"**record_id:** `{record['record_id']}`")
        st.write("**Original question:**")
        st.write(record["question"])
        st.write("**Ground truth / answer:**")
        st.write(record["ground_truth"] or "N/A")
        st.write("**Joined context preview:**")
        st.text_area(
            "Context preview",
            value=record["joined_context"][:1600],
            height=220,
            label_visibility="collapsed",
        )

        if st.button("Hỏi bằng câu hỏi này", type="primary", key="dataset_ask"):
            with st.spinner("Đang query bằng câu hỏi từ dataset..."):
                try:
                    answer, chunks = run_query(record["question"], strategy, top_k)
                except Exception as exc:
                    st.error(f"Lỗi query: {exc}")
                else:
                    render_answer(answer, chunks, ground_truth=record["ground_truth"])
    else:
        st.warning("Không có record hợp lệ trong subset hiện tại.")

with benchmark_tab:
    benchmark_path = Path("benchmark_results.csv")
    if benchmark_path.exists():
        benchmark_df = pd.read_csv(benchmark_path)
        st.warning(
            "Đây là evaluation-lite trên tập nhỏ, chưa phải full RAGAS. "
            "Kết quả dùng để kiểm tra nhanh retrieval behavior trong MVP.",
            icon="⚠️",
        )

        required_columns = [
            "strategy",
            "evaluation_type",
            "sample_count",
            "top1_hit_rate",
            "topk_hit_rate",
            "avg_distance",
            "answer_keyword_overlap",
            "avg_score",
            "note",
        ]
        available_columns = [
            column for column in required_columns
            if column in benchmark_df.columns
        ]

        numeric_columns = [
            "sample_count",
            "top1_hit_rate",
            "topk_hit_rate",
            "avg_distance",
            "answer_keyword_overlap",
            "avg_score",
        ]
        for column in numeric_columns:
            if column in benchmark_df.columns:
                benchmark_df[column] = pd.to_numeric(benchmark_df[column], errors="coerce")

        if "strategy" in benchmark_df.columns and "avg_score" in benchmark_df.columns:
            best_row = benchmark_df.sort_values("avg_score", ascending=False).iloc[0]
            st.success(
                f"Chiến lược tốt nhất theo avg_score hiện tại: "
                f"{best_row['strategy']} ({best_row['avg_score']:.4f})"
            )

        st.subheader("Bảng kết quả benchmark")
        st.dataframe(
            benchmark_df[available_columns],
            use_container_width=True,
            hide_index=True,
        )

        if "strategy" in benchmark_df.columns and "avg_score" in benchmark_df.columns:
            st.subheader("Biểu đồ avg_score theo strategy")
            chart_df = benchmark_df[["strategy", "avg_score"]].dropna()
            st.bar_chart(chart_df.set_index("strategy")["avg_score"])
    else:
        st.info("Benchmark RAGAS chưa chạy. MVP hiện tại đã hoàn thành verify, indexing và query pipeline.")
