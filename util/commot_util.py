import pandas as pd
import streamlit as st
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import io

st.title("공통 기능")


st.subheader("엑셀 업로드/다운로드 기능")


with st.container():
    _, col1, col2, col3 = st.columns([5, 3, 2.45, 2.5])

    with col1:
        st.download_button(
            "템플릿 다운로드",
            data=Path("data/template.xlsx").read_bytes(),
            file_name="template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        uploaded = None
        with st.popover("엑셀 업로드"):
            uploaded = st.file_uploader(
                "파일 선택",
                type=["xlsx"],
                label_visibility="collapsed",
            )

    # 업로드 전: 빈 테이블 + 다운로드 비활성화
    if uploaded is None:
        st.dataframe(pd.DataFrame(), use_container_width=True, height=500)

        with col3:
            st.button("엑셀 다운로드", disabled=True, use_container_width=True)
    else:

        # 업로드 후
        df = pd.read_excel(uploaded)
        st.dataframe(df, use_container_width=True, height=500)

        # DataFrame → Excel bytes
        def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="data")
            return buffer.getvalue()

        excel_bytes = df_to_excel_bytes(df)

        with col3:
            st.download_button(
                "엑셀 다운로드",
                data=excel_bytes,
                file_name="result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
st.divider()
with st.container():
    st.subheader("barplot")

    df = pd.read_excel('data/template.xlsx')
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(
        data=df,
        x=df['구매총액'],
        y=df.index,
        estimator="mean",   # 평균
        errorbar=None,      # 신뢰구간 제거 (깔끔)
        ax=ax,
    )

    st.pyplot(fig)