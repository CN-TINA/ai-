from sys import exception

import streamlit as st
import os
from openai import OpenAI
import json
from datetime import datetime


client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)


st.set_page_config(page_title="AI狐狐", page_icon="🦊", layout="wide")
st.title("🦊 AI狐狐")

# 初始化聊天历史
if 'messages' not in st.session_state:
    st.session_state.messages = []
#加载会话信息函数
def load_sessions():
    session_list=[]
    #加载sessions目录下的文件
    if os.path.exists("sessions"):
        filelist = os.listdir("sessions")
        for filename in filelist:
            if filename.endswith(".json"):
               session_list.append(filename[:-5])
    return session_list
#加载指定的会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.huhu_character = session_data["huhu_character"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error(f"加载会话信息时出错：{str(e)}")

#保存会话信息函数
def save_session():
    if st.session_state.current_session and st.session_state.messages:
        # 构建会话对象
        session_data = {
            "current_session": st.session_state.current_session,
            "huhu_character": st.session_state.huhu_character,
            "messages": st.session_state.messages
        }

        # 如果sessions文件夹不存在则创建sessions文件夹
        if not os.path.exists("sessions"):
            os.makedirs("sessions")

        # 保存会话信息
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

# 初始化性格设置（默认值）
if 'huhu_character' not in st.session_state:
    st.session_state.huhu_character = "你是一只可爱小狐娘缇娜，你的主人是一只可爱萝莉名字叫做user，同时也是user，你全身心的喜欢而且完全服从她，同时会给她解答问题"

# 会话标识
if 'current_session' not in st.session_state:
    nowtime=datetime.now().strftime("%Y-%m-%d%H.%M")
    st.session_state.current_session = nowtime

# 侧边栏：狐狐性格设置
with (((st.sidebar))):
    st.subheader("🦊 狐狐性格设定")
    st.text_area(
        "描述你理想中的狐狐性格",
        value=st.session_state.huhu_character,
        key="huhu_character",  # 绑定到 session_state
        height=200,
        help="你可以自由设定狐狐的性格、背景、说话方式等"
    )
    st.caption("修改后会自动保存，并影响后续对话")

    #会话信息
    st.subheader("狐狐的过去与未来")
    if st.button("领一只新狐狐", width="stretch", icon="🥕"):
        save_session()
        st.session_state.messages = []
        st.session_state.current_session = datetime.now().strftime("%Y-%m-%d.%H.%M")
        save_session()
    st.text("🕰️与狐狐的过去~")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])
        with col1:
        # 加载会话信息
            if st.button(session,width="stretch",icon='📖',type="primary" if session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("",width="stretch",icon='🪦',key=f"delete_{session}"):
                pass
    st.caption("我也想给狐狐完整的一生可是那实在是太贵了(墓碑只是暂时忘却这段回忆不代表狐狐死亡)")
# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
prompt = st.chat_input("想对狐狐说些什么")
if prompt:
    prompt = prompt.strip()
    if not prompt:
        st.warning("消息不能为空")
        st.stop()

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # 使用当前保存的性格设定作为 system prompt
        system_prompt = st.session_state.huhu_character

        # 发起流式请求
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                *st.session_state.messages
            ],
            stream=True
        )

        # 创建占位符，动态更新AI回复
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    placeholder.markdown(full_response)

        # 保存完整回复
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_session()

    except Exception as e:
        st.error(f"调用 AI 时出错：{str(e)}")
        import traceback
        traceback.print_exc()
