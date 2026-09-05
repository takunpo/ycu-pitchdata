import streamlit as st
import pandas as pd
import datetime
import os
import json

st.set_page_config(layout="wide", page_title="投球データ入力アプリ")

# ==========================================
# 🎨 UIデザインの最適化（縦幅を詰めるCSS）
# ==========================================
st.markdown("""
<style>
/* ラジオボタンのタイトルと選択肢を強制的に横並びにする */
div[data-testid="stRadio"] {
    display: flex;
    flex-direction: row;
    align-items: center;
}
div[data-testid="stRadio"] > label {
    margin-bottom: 0px !important;
    margin-right: 15px;
    min-width: 65px; /* B 🟢 などの文字幅を揃えて縦のラインを綺麗にする */
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 パスワード保護の仕組み
# ==========================================
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔒 パスワードを入力してね")
    pwd = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if pwd == "ycujunko": 
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("パスワードが違うよ！")
    st.stop() 
# ==========================================

st.title("⚾ 一球速報システム")

CSV_FILE = "pitch_log_v6.csv"
DB_FILE = "teams_db.json"

if "teams_db" not in st.session_state:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            st.session_state["teams_db"] = json.load(f)
    else:
        st.session_state["teams_db"] = {}

def save_teams_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state["teams_db"], f, ensure_ascii=False, indent=4)

if "selected_loc" not in st.session_state:
    st.session_state["selected_loc"] = "5"

def update_loc(loc):
    st.session_state["selected_loc"] = loc

def save_data(new_data):
    df = pd.DataFrame([new_data])
    if not os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(CSV_FILE, mode='a', header=False, index=False, encoding="utf-8-sig")

col1, col2 = st.columns([1, 1])

with col1:
    is_empty = len(st.session_state["teams_db"]) == 0
    with st.expander("➕ チーム・選手の登録 / 🗑️ 削除", expanded=is_empty):
        tab1, tab2, tab3 = st.tabs(["チーム追加", "選手追加", "データ削除"])
        
        with tab1:
            new_team = st.text_input("新しいチーム名")
            if st.button("チームを追加する"):
                if new_team:
                    if new_team not in st.session_state["teams_db"]:
                        st.session_state["teams_db"][new_team] = {"投手": [], "捕手": [], "野手": []}
                        save_teams_db()
                        st.success(f"チーム【{new_team}】を追加したよ！")
                        st.rerun()
                    else:
                        st.warning("そのチームは既に登録されているよ。")
                else:
                    st.warning("チーム名を入力してね。")

        all_teams = list(st.session_state["teams_db"].keys())
        
        with tab2:
            if all_teams:
                reg_team = st.selectbox("登録先チーム", all_teams, key="reg_team")
                reg_position = st.selectbox("ポジション区分", ["投手", "捕手", "野手"])
                reg_name = st.text_input("選手名")
                if st.button("選手を追加する"):
                    if reg_name:
                        if reg_name not in st.session_state["teams_db"][reg_team][reg_position]:
                            st.session_state["teams_db"][reg_team][reg_position].append(reg_name)
                            save_teams_db()
                            st.success(f"{reg_team}の{reg_position}に【{reg_name}】を追加したよ！")
                            st.rerun()
                        else:
                            st.warning("その選手は既に登録されているよ。")
                    else:
                        st.warning("選手名を入力してね。")
            else:
                st.info("まずは「チーム追加」タブからチームを登録してね！")

        with tab3:
            if all_teams:
                del_type = st.radio("削除する種類", ["選手を削除", "チームごと削除"], horizontal=True)
                
                if del_type == "選手を削除":
                    del_team = st.selectbox("チームを選択", all_teams, key="del_team")
                    del_position = st.selectbox("ポジションを選択", ["投手", "捕手", "野手"], key="del_pos")
                    del_players = st.session_state["teams_db"][del_team][del_position]
                    
                    if del_players:
                        del_name = st.selectbox("削除する選手", del_players)
                        if st.button("この選手を削除する"):
                            st.session_state["teams_db"][del_team][del_position].remove(del_name)
                            save_teams_db()
                            st.success(f"【{del_name}】を削除したよ。")
                            st.rerun()
                    else:
                        st.write("このポジションには誰も登録されていないよ。")
                        
                elif del_type == "チームごと削除":
                    del_team_all = st.selectbox("削除するチーム", all_teams, key="del_team_all")
                    st.warning(f"※チーム【{del_team_all}】と所属する全選手が消えます")
                    if st.button("このチームを完全に削除する"):
                        del st.session_state["teams_db"][del_team_all]
                        save_teams_db()
                        st.success(f"チーム【{del_team_all}】を削除したよ。")
                        st.rerun()
            else:
                st.info("登録されているデータがないよ。")

    st.markdown("---")
    
    if not all_teams:
        st.info("👆 まずは上のメニューから、対戦するチームと選手を登録してね！")
    else:
        st.subheader("🛠️ 1. 試合・チーム設定")
        
        team_col1, team_col2 = st.columns(2)
        with team_col1:
            batting_team = st.selectbox("攻撃チーム（打者側）", all_teams, index=0)
        with team_col2:
            default_fielding_idx = 1 if len(all_teams) > 1 and batting_team == all_teams[0] else 0
            fielding_team = st.selectbox("守備チーム（投手・捕手側）", all_teams, index=default_fielding_idx)

        st.markdown("---")
        st.subheader("🚦 2. 状況設定（打席開始時）")
        
        in_col1, in_col2 = st.columns(2)
        with in_col1:
            inning_num = st.number_input("イニング", min_value=1, max_value=12, value=1)
        with in_col2:
            inning_tb = st.radio("表/裏", ["表", "裏"], horizontal=True)
        inning = f"{inning_num}回{inning_tb}"
        
        st.write("▼ ランナー状況")
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1: r1 = st.checkbox("1塁")
        with r_col2: r2 = st.checkbox("2塁")
        with r_col3: r3 = st.checkbox("3塁")
        runner_state = f"{'1塁' if r1 else ''}{'2塁' if r2 else ''}{'3塁' if r3 else ''}"
        if runner_state == "":
            runner_state = "ランナーなし"

        pitcher_list = st.session_state["teams_db"][fielding_team]["投手"]
        catcher_list = st.session_state["teams_db"][fielding_team]["捕手"]
        batter_list = st.session_state["teams_db"][batting_team]["野手"]
        
        st.write("▼ 選手設定")
        match_col1, match_col2, match_col3 = st.columns(3)
        with match_col1:
            pitcher = st.selectbox("投手（守備側）", pitcher_list if pitcher_list else ["未登録"])
        with match_col2:
            catcher = st.selectbox("捕手（守備側）", catcher_list if catcher_list else ["未登録"])
        with match_col3:
            batter = st.selectbox("打者（攻撃側）", batter_list if batter_list else ["未登録"])

        st.markdown("---")
        st.subheader("🎯 3. 対戦・投球入力（1球ごと）")
        
        st.write("▼ カウント (BSO)")
        balls = st.radio("B 🟢", ["0", "1", "2", "3"], horizontal=True)
        strikes = st.radio("S 🟡", ["0", "1", "2"], horizontal=True)
        outs = st.radio("O 🔴", ["0", "1", "2"], horizontal=True)
        
        st.write("▼ 投球内容")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            pitch_type = st.selectbox("球種", ["FF(ストレート)", "FT(ツーシーム)", "SL(スライダー)", "FC(カット)", "CU(カーブ)", "FS(フォーク)", "CH(チェンジアップ)", "OT(その他)"])
        with p_col2:
            pitch_speed = st.number_input("球速 (km/h)", min_value=50, max_value=200, value=130, step=1)
        with p_col3:
            pitch_result = st.selectbox("投球結果", ["S(見逃し)", "SS(空振り)", "B(ボール)", "F(ファウル)", "BIP(インプレー)"])
        
        st.markdown("---")
        st.write("📍 **コース入力（ボタンを押して選択）**")
        
        st.info(f"現在の選択コース: 【 {st.session_state['selected_loc']} 】")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("1 (左上)", on_click=update_loc, args=("1",), use_container_width=True)
            st.button("4 (左中)", on_click=update_loc, args=("4",), use_container_width=True)
            st.button("7 (左下)", on_click=update_loc, args=("7",), use_container_width=True)
        with c2:
            st.button("2 (中上)", on_click=update_loc, args=("2",), use_container_width=True)
            st.button("5 (ど真ん中)", on_click=update_loc, args=("5",), use_container_width=True)
            st.button("8 (中下)", on_click=update_loc, args=("8",), use_container_width=True)
        with c3:
            st.button("3 (右上)", on_click=update_loc, args=("3",), use_container_width=True)
            st.button("6 (右中)", on_click=update_loc, args=("6",), use_container_width=True)
            st.button("9 (右下)", on_click=update_loc, args=("9",), use_container_width=True)
            
        st.write("ボールゾーン")
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("11(高め)", on_click=update_loc, args=("11",), use_container_width=True)
        with b2: st.button("12(低め)", on_click=update_loc, args=("12",), use_container_width=True)
        with b3: st.button("13(左)", on_click=update_loc, args=("13",), use_container_width=True)
        with b4: st.button("14(右)", on_click=update_loc, args=("14",), use_container_width=True)

        st.markdown("---")
        memo = st.text_input("メモ（打球方向や詳細など自由記述）")
        
        if st.button("🚀 この1球を記録する！", type="primary", use_container_width=True):
            new_record = {
                "date": datetime.date.today(),
                "inning": inning,
                "batting-team": batting_team,
                "fielding-team": fielding_team,
                "pitcher": pitcher,
                "catcher": catcher,
                "batter": batter,
                "ball-count": balls,
                "strike-count": strikes,
                "out-count": outs,
                "runners": runner_state,
                "pitch-type": pitch_type.split("(")[0],
                "pitch-speed": pitch_speed,
                "location": st.session_state["selected_loc"],
                "pitch-result": pitch_result.split("(")[0],
                "memo": memo
            }
            save_data(new_record)
            st.success("記録したよ！")
            st.rerun()

with col2:
    st.subheader("📊 リアルタイム一球速報ログ")
    
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        
        st.write("▼ 直近の投球履歴")
        for idx, row in df.tail(5).iloc[::-1].iterrows():
            inn_str = row['inning'] if 'inning' in row else ''
            
            b_val = row['ball-count'] if 'ball-count' in row else '-'
            s_val = row['strike-count'] if 'strike-count' in row else '-'
            o_val = row['out-count'] if 'out-count' in row else '-'
            
            speed_str = f"{row['pitch-speed']}km/h" if 'pitch-speed' in row and pd.notna(row['pitch-speed']) else ""
            
            st.info(f"【{inn_str} {o_val}死 {row['runners']} (B{b_val}-S{s_val})】 {row['fielding-team']}（投:{row['pitcher']}） vs {row['batting-team']}（打:{row['batter']}） ｜ {row['pitch-type']} {speed_str} (コース:{row['location']}) ➡️ {row['pitch-result']} （{row['memo'] if pd.notna(row['memo']) else ''}）")
        
        st.markdown("---")
        st.write("▼ データ一覧（最新10件）")
        st.dataframe(df.tail(10).iloc[::-1], use_container_width=True)
        
        st.markdown("---")
        with open(CSV_FILE, "rb") as file:
            st.download_button(
                label="📥 溜まったデータをCSVでダウンロード",
                data=file,
                file_name="pitch_log_v6.csv",
                mime="text/csv"
            )
    else:
        st.info("まだデータがないよ。左の画面から最初の1球を入力してみてね！")