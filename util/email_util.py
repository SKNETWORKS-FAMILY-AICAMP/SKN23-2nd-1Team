import smtplib
from email.message import EmailMessage
import streamlit as st

ALERT_TO = "skn23gpt@gmail.com"

def send_hardcoded_alert_with_excel(
    subject: str,
    html_body: str,
    excel_bytes: bytes,
    filename: str = "result.xlsx",
):
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ALERT_TO

    msg.set_content("이 메일은 HTML을 포함합니다.")
    msg.add_alternative(html_body, subtype="html")

    # 엑셀 첨부
    msg.add_attachment(
        excel_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
