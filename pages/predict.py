import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import pandas as pd
import json
import ast
import util.review_api as ra
from util.loading import loading_on
from util.global_style import load_global_css
from util.global_style import apply_global_style
import util.excel_util as eu
import util.email_util as emu
    
##
# Date        Description   Authur
# 2026-01-11  최초생성      created by 양창일
##
# css
load_global_css()
apply_global_style("images/library_hero 3.jpg")

# 데이터셋 불러오기
df = pd.read_csv("data/steam_top100_assets_3rd_trimmed.csv")

# 형변환
df["appid"] = df["appid"].astype("int64")
df["game_name"] = df["game_name"].astype(str)

# 딕셔너리화
appid_to_name = dict(zip(df["appid"].tolist(), df["game_name"].tolist()))
options = list(appid_to_name.keys())

st.subheader("게임별 이탈률 예측")

selected_appid = st.selectbox(
    "게임 선택",
    options=options,
    format_func=lambda x: appid_to_name[x],
)

# 선택된 appid로 df에서 한 줄 찾기
row = df.loc[df["appid"] == selected_appid].iloc[0]
title = row["game_name"]   # 필요한 값 꺼내기 (여기서 더 꺼내면 됨)

VIDEO_URL = row["microtrailer_url"]
THUMB_URL = row["image_url"]
raw_tags = row["tags"]
STORE_URL = row["store_url"]
if isinstance(raw_tags, str):
    try:
        TAGS = json.loads(raw_tags)
    except Exception:
        TAGS = ast.literal_eval(raw_tags)
else:
    TAGS = raw_tags                           # 이미 list면 그대로

tags_html = "".join(f"<span>{t}</span>" for t in TAGS)

css = Path("styles/predict.css").read_text(encoding="utf-8")
with st.container():
    html_code = f"""
    <style>
    {css}
    </style>
    <div class="wrap">
    <a href="{STORE_URL}" target="_blank" rel="noopener noreferrer" class="card-link">
    <div class="container">
        <div class="video-clip">
        <div class="video-bg">
            <video autoplay muted loop playsinline>
            <source src="{VIDEO_URL}" type="video/webm">
            </video>

            <div class="info">
            <div class="info-grid">
                <img class="thumb" src="{THUMB_URL}" alt="thumb"/>
                <div class="text">
                <h2 class="title">{title}</h2>
                <div class="tags">{tags_html}</div>
                </div>
            </div>
            </div>

        </div>
        </div>
    </div>
    </a>
    </div>
    """

    #components.html(html_code, height=700)


with st.container(border=True):
    st.subheader("리뷰 단건 예측")
    st.write("*최근 작성된 STEAM 리뷰를 예측합니다.")
    user_id = st.text_input("Steam ID를 입력하세요")
    if user_id:
        if not user_id.isdigit():
            st.error("Steam ID는 숫자만 입력해주세요.")
        else:
            steam_id = int(user_id)
                    # API 실행
            review = ra.run_batch([selected_appid], days=0, max_workers=4)

            if not review:
                st.warning("수집된 리뷰가 없습니다.")
            else :
                # df만 뽑아서 concat
                df_review = pd.concat(
                    [df for _, df in review],
                    ignore_index=True
                )
                steam_id = int(steam_id)
                df_review["steamid"] = df_review["steamid"].astype(int)
                df_review = df_review[df_review['steamid']==steam_id]

                st.subheader("리뷰 예측")
                styled = df_review.style.set_properties(**{
                    "background-color": "#1b2838",   # Steam 다크 블루
                    "color": "#c7d5e0"               # Steam 글자색
                })
                st.dataframe(styled, use_container_width=True, hide_index=True)
                
                # session_state 저장
                st.session_state["one_review_df"] = df_review
with st.container(border=True):
    st.subheader("실시간 리뷰 예측")
    st.write("*실시간 하루단위의 STEAM 리뷰를 예측합니다.")
    # 하루치 리뷰 데이터 API
    def one_day_review(app_id):

        app_id_list = [app_id]
        
        # API 실행
        review_list = ra.run_batch(app_id_list, days=1, max_workers=4)

        if not review_list:
            st.warning("수집된 리뷰가 없습니다.")
            return

        # df만 뽑아서 concat
        df_all = pd.concat(
            [df for _, df in review_list],
            ignore_index=True
        )
        # session_state 저장
        st.session_state["one_day_review_df"] = df_all

    clicked = st.button(
        "리뷰 가져오기",
        on_click=one_day_review,
        args=(selected_appid,)
    )
    
    if "one_day_review_df" in st.session_state:
        df_result = st.session_state["one_day_review_df"]

        if df_result is None or df_result.empty:
            st.warning("수집된 리뷰가 없습니다.")
        else:
            st.subheader("리뷰 예측")
            styled = df_result.style.set_properties(**{
                "background-color": "#1b2838",   # Steam 다크 블루
                "color": "#c7d5e0"               # Steam 글자색
            })
            st.dataframe(styled, use_container_width=True, hide_index=True)
            excel_bytes = eu.df_to_excel_bytes(styled)

            # 하드 코딩 제목/본문
            SUBJECT = "[Steam Churn] 엑셀 예측 결과 리포트"
            HTML_BODY = f"""
            <h2>Steam 이탈률 예측 결과</h2>
            <p>게임: <b>{title}</b></p>
            <p>첨부된 엑셀에 예측 결과가 포함되어 있습니다.</p>
            <p>- 자동 발송 시스템</p>
            """

            if st.button("📧 결과 엑셀 이메일로 보내기", use_container_width=True):
                emu.send_hardcoded_alert_with_excel(
                    subject=SUBJECT,
                    html_body=HTML_BODY,
                    excel_bytes=excel_bytes,
                    filename="steam_churn_result.xlsx",
                )
                st.success("📧 이메일로 엑셀 첨부 전송 완료!")

with st.container(border=True):
    st.subheader("엑셀 업로드로 예측")

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
        #st.dataframe(pd.DataFrame(), use_container_width=True, height=500)

        with col3:
            st.button("엑셀 다운로드", disabled=True, use_container_width=True)
    else:

        # 업로드 후
        df = pd.read_excel(uploaded)
        styled = df.style.set_properties(**{
            "background-color": "#1b2838",   # Steam 다크 블루
            "color": "#c7d5e0"               # Steam 글자색
        })
        st.dataframe(styled, use_container_width=True, hide_index=True)

        excel_bytes = eu.df_to_excel_bytes(df)

        with col3:
            st.download_button(
                "엑셀 다운로드",
                data=excel_bytes,
                file_name="result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )