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
import util.model_predict as mp
import joblib
from util.set_util import set_page
set_page("Predict")
##
# Date        Description   Authur
# 2026-01-11  최초생성      created by 양창일
# 2026-01-13  예측추가      modified by 양창일
##
# css
load_global_css()
apply_global_style("images/library_hero 3.jpg")

# 데이터셋 불러오기
df = pd.read_csv("data/steam_top50_assets_3rd_trimmed.csv")

# 형변환
df["appid"] = df["appid"].astype("int64")
df["game_name"] = df["game_name"].astype(str)

# 딕셔너리화
appid_to_name = dict(zip(df["appid"].tolist(), df["game_name"].tolist()))
options = list(appid_to_name.keys())

st.title("게임별 이탈률 예측")

selected_appid = st.selectbox(
    "게임 선택",
    options=options,
    format_func=lambda x: appid_to_name[x],
)

# 선택된 appid로 df에서 한 줄 찾기
row = df.loc[df["appid"] == selected_appid].iloc[0]
title = row["game_name"]  

VIDEO_URL = row["microtrailer_url"]
THUMB_URL = row["image_url"]
raw_tags = row["tags"]
STORE_URL = row["store_url"]

model_name = f"model_{selected_appid}"
bundle = joblib.load(f"models/{model_name}.pkl")
# bundle이 dict면 bundle['model'], 아니면 bundle 자체가 모델
model = bundle["model"] if isinstance(bundle, dict) else bundle

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

    components.html(html_code, height=700)
with st.container(border=True):
    st.subheader("실시간 리뷰 예측")
    st.write("*실시간 하루 단위의 STEAM 리뷰를 예측합니다.*")
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
            churn_full_list_df, churn_view_list_df = mp.churn_predict(df_result,model)
            styled_view = churn_view_list_df.style.set_properties(**{
                "background-color": "#1b2838",   # Steam 다크 블루
                "color": "#c7d5e0"               # Steam 글자색
            })
            styled_full = churn_full_list_df.style.set_properties(**{
                "background-color": "#1b2838",   # Steam 다크 블루
                "color": "#c7d5e0"               # Steam 글자색
            })
            st.dataframe(styled_view, use_container_width=True, hide_index=True)
            
            
            
            excel_bytes = eu.df_to_excel_bytes(styled_full)

            # 제목/본문
            SUBJECT = "[Steam Churn] 엑셀 예측 결과 리포트"
            HTML_BODY = f"""
            <h2>Steam 이탈률 예측 결과</h2>
            <p>게임: <b>{title}</b></p>
            <p>첨부된 엑셀에 예측 결과가 포함되어 있습니다.</p>
            <p>- 자동 발송 시스템</p>
            """

            if st.button("결과 엑셀 이메일로 보내기", use_container_width=True):
                emu.send_hardcoded_alert_with_excel(
                    subject=SUBJECT,
                    html_body=HTML_BODY,
                    excel_bytes=excel_bytes,
                    filename="steam_churn_result.xlsx",
                )
                st.success("이메일로 엑셀 첨부 전송 완료!")

with st.container(border=True):
    st.subheader("리뷰 단건 예측")
    st.write("*최근 작성된 STEAM 리뷰를 예측합니다.*")

    user_id = st.text_input("Steam ID를 입력하세요")

    if user_id:
        if not user_id.isdigit():
            st.error("Steam ID는 숫자만 입력해주세요.")
        else:
            steam_id = int(user_id)

            # API 실행 (list 반환)
            review = ra.run_batch([selected_appid], days=0, max_workers=4)

            # 1) run_batch 결과(list) 자체가 비었는지
            if not review:
                st.warning("수집된 리뷰가 없습니다.")
            else:
                # 2) list -> DataFrame 합치기 (빈 DF 방지)
                dfs = [df for _, df in review if df is not None and not df.empty]
                if not dfs:
                    st.warning("수집된 리뷰가 없습니다.")
                else:
                    df_review = pd.concat(dfs, ignore_index=True)

                    # 3) steamid 컬럼 존재/형 변환/필터
                    if "steamid" not in df_review.columns:
                        st.error("수집된 데이터에 steamid 컬럼이 없습니다.")
                    else:
                        df_review["steamid"] = pd.to_numeric(df_review["steamid"], errors="coerce").astype("Int64")
                        df_review = df_review[df_review["steamid"] == steam_id].copy()

                        # 4) 필터 이후 비었으면 예측 호출 금지 (LightGBM 에러 방지)
                        if df_review.empty:
                            st.warning("해당 Steam ID의 리뷰가 없습니다.")
                        else:
                            st.subheader("리뷰 예측")

                            churn_full_df, churn_view_df = mp.churn_predict(df_review, model)

                            # churn_predict가 빈 DF를 반환하는 경우도 대비
                            if churn_view_df is None or (
                                hasattr(churn_view_df, "empty") and churn_view_df.empty
                            ):
                                st.warning("예측 결과가 없습니다.")
                            else:
                                styled = churn_view_df.style.set_properties(**{
                                    "background-color": "#1b2838",
                                    "color": "#c7d5e0",
                                })
                                st.dataframe(styled, use_container_width=True, hide_index=True)

                                # session_state 저장
                                st.session_state["one_review_df"] = churn_view_df



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
        df_excel = pd.read_excel(uploaded)
        churn_full_excel_df, churn_view_excel_df = mp.churn_predict(df_excel,model)

        styled_excel_view = churn_view_excel_df.style.set_properties(**{
            "background-color": "#1b2838",   # Steam 다크 블루
            "color": "#c7d5e0"               # Steam 글자색
        })
        styled_excel_full = churn_full_excel_df.style.set_properties(**{
            "background-color": "#1b2838",   # Steam 다크 블루
            "color": "#c7d5e0"               # Steam 글자색
        })
        
        st.dataframe(styled_excel_view, use_container_width=True, hide_index=True)

        excel_bytes = eu.df_to_excel_bytes(styled_excel_full)

        with col3:
            st.download_button(
                "엑셀 다운로드",
                data=excel_bytes,
                file_name="result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )