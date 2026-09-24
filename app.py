import streamlit as st
import pandas as pd
import datetime
import os
import json
from supabase import create_client, Client

st.set_page_config(layout="wide", page_title="投球データ入力アプリ")

# ==========================================
# 🚀 Supabase連携の設定
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"データベースの接続に失敗しました: {e}")
    st.stop()

# ==========================================
# 🎨 UIデザインの最適化
# ==========================================
st.markdown("""
<style>
div[data-testid="stRadio"] {
    display: flex;
    flex-direction: row;
    align-items: center;
}
div[data-testid="stRadio"] > label {
    margin-bottom: 0px !important;
    margin-right: 15px;
    min-width: 65px; 
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 パスワード保護の仕組み
# ==========================================
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔒 パスワードを入力してください")
    pwd = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if pwd == "ycujunko": 
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("パスワードが違います。")
    st.stop() 
# ==========================================

st.title("⚾ チーム別フィルタ対応・一球速報システム")

# ==========================================
# チーム情報の管理（Supabase対応）
# ==========================================
def load_teams_db():
    try:
        response = supabase.table("teams_data").select("data").eq("id", 1).execute()
        if len(response.data) > 0:
            return response.data[0]["data"]
        else:
            return {}
    except:
        return {}

def save_teams_db_to_supabase(data_dict):
    try:
        # すでにデータがあるか確認
        check = supabase.table("teams_data").select("id").eq("id", 1).execute()
        if len(check.data) > 0:
            # 上書き更新
            supabase.table("teams_data").update({"data": data_dict}).eq("id", 1).execute()
        else:
            # 新規作成
            supabase.table("teams_data").insert({"id": 1, "data": data_dict}).execute()
    except Exception as e:
        st.error(f"チームデータの保存に失敗しました: {e}")

if "teams_db" not in st.session_state:
    st.session_state["teams_db"] = load_teams_db()

def save_teams_db():
    save_teams_db_to_supabase(st.session_state["teams_db"])

if "selected_loc" not in st.session_state:
    st.session_state["selected_loc"] = "5"

def update_loc(loc):
    st.session_state["selected_loc"] = loc

# ==========================================
# 投球データの保存（Supabase対応）
# ==========================================
def save_data(new_data):
    try:
        # 'date'オブジェクトを文字列に変換
        if isinstance(new_data.get("date"), datetime.date):
            new_data["date"] = new_data["date"].isoformat()
            
        supabase.table("pitch_logs").insert(new_data).execute()
    except Exception as e:
        st.error(f"データの保存に失敗しました: {e}")

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
                        st.success(f"チーム【{new_team}】を追加しました。")
                        st.rerun()
                    else:
                        st.warning("そのチームは既に登録されています。")
                else:
                    st.warning("チーム名を入力してください。")

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
                            st.success(f"{reg_team}の{reg_position}に【{reg_name}】を追加しました。")
                            st.rerun()
                        else:
                            st.warning("その選手は既に登録されています。")
                    else:
                        st.warning("選手名を入力してください。")
            else:
                st.info("まずは「チーム追加」タブからチームを登録してください。")

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
                            st.success(f"【{del_name}】を削除しました。")
                            st.rerun()
                    else:
                        st.write("このポジションには誰も登録されていません。")
                        
                elif del_type == "チームごと削除":
                    del_team_all = st.selectbox("削除するチーム", all_teams, key="del_team_all")
                    st.warning(f"※チーム【{del_team_all}】と所属する全選手が消えます")
                    if st.button("このチームを完全に削除する"):
                        del st.session_state["teams_db"][del_team_all]
                        save_teams_db()
                        st.success(f"チーム【{del_team_all}】を削除しました。")
                        st.rerun()
            else:
                st.info("登録されているデータがありません。")
                
    st.markdown("---")
    
    if not all_teams:
        st.info("👆 まずは上のメニューから、対戦するチームと選手を登録してください。")
    else:
        st.subheader("🛠️ 1. 試合・チーム設定")

        match_date = st.date_input("試合日", value=datetime.date.today())
        
        team_col1, team_col2 = st.columns(2)
        with team_col1:
            batting_team = st.selectbox("攻撃チーム（打者側）", all_teams, index=0)
        with team_col2:
            default_fielding_idx = 1 if len(all_teams) > 1 and batting_team == all_teams[0] else 0
            fielding_team = st.selectbox("守備チーム（投手・捕手側）", all_teams, index=default_fielding_idx)

        st.markdown("---")
        st.subheader("🚦 2. 状況設定（打席開始時）")
        
        inning_num = st.number_input("イニング", min_value=1, max_value=12, value=1)
        inning = str(inning_num)
        
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
            speed_container = st.empty() 
            speed_unknown = st.checkbox("球速不明", value=False) 
            pitch_speed_input = speed_container.number_input("球速 (km/h)", min_value=50, max_value=200, value=130, step=1, disabled=speed_unknown)
            
            final_pitch_speed = "" if speed_unknown else str(pitch_speed_input)

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
                "date": match_date,
                "inning": inning,
                "batting_team": batting_team,
                "fielding_team": fielding_team,
                "pitcher": pitcher,
                "catcher": catcher,
                "batter": batter,
                "ball_count": balls,
                "strike_count": strikes,
                "out_count": outs,
                "runners": runner_state,
                "pitch_type": pitch_type.split("(")[0],
                "pitch_speed": final_pitch_speed,
                "location": st.session_state["selected_loc"],
                "pitch_result": pitch_result.split("(")[0],
                "memo": memo
            }
            save_data(new_record)
            st.success("データベースに記録しました。")
            st.rerun()

with col2:
    st.subheader("📊 リアルタイム一球速報ログ")
    
    # Supabaseからデータを取得して表示
    try:
        response = supabase.table("pitch_logs").select("*").order("id", desc=True).limit(50).execute()
        db_data = response.data
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        db_data = []
    
    if len(db_data) > 0:
        df = pd.DataFrame(db_data)
        
        st.write("▼ 直近の投球履歴")
        for idx, row in df.head(5).iterrows():
            inn_str = row.get('inning', '')
            b_val = row.get('ball_count', '-')
            s_val = row.get('strike_count', '-')
            o_val = row.get('out_count', '-')
            
            speed_val = row.get('pitch_speed', '')
            speed_str = f"{speed_val}km/h" if speed_val else "速度不明"
            memo_val = row.get('memo', '')
            memo_str = f"（{memo_val}）" if memo_val else ""
            
            st.info(f"【{inn_str} {o_val}死 {row.get('runners','')} (B{b_val}-S{s_val})】 {row.get('fielding_team','')}（投:{row.get('pitcher','')}） vs {row.get('batting_team','')}（打:{row.get('batter','')}） ｜ {row.get('pitch_type','')} {speed_str} (コース:{row.get('location','')}) ➡️ {row.get('pitch_result','')} {memo_str}")
        
        st.markdown("---")
        st.write("▼ データ一覧（最新50件まで）")
        
        # 編集対象の列を指定
        display_df = df[['id', 'date', 'inning', 'pitcher', 'batter', 'pitch_type', 'pitch_speed', 'pitch_result', 'memo']]
        
        edited_df = st.data_editor(
            display_df, 
            num_rows="dynamic",
            use_container_width=True,
            disabled=["id"] # id列は変更できないようにロック
        )
        
        if st.button("💾 編集内容をデータベースに保存する"):
            try:
                # 削除された行の処理
                original_ids = set(df['id'])
                edited_ids = set(edited_df['id'].dropna())
                deleted_ids = original_ids - edited_ids
                
                for del_id in deleted_ids:
                    supabase.table("pitch_logs").delete().eq("id", del_id).execute()
                
                # 更新された行の処理
                for idx, row in edited_df.iterrows():
                    # 欠損値(NaN)を除外して辞書化
                    update_data = {k: v for k, v in row.items() if pd.notna(v) and k != 'id'}
                    # 文字列型に強制変換（エラー回避）
                    # 文字列型に強制変換（エラー回避）
                    if 'pitch_speed' in update_data:
                        update_data['pitch_speed'] = str(update_data['pitch_speed'])
                    # ▼日付を編集した時用のエラー回避処理を追加▼
                    if 'date' in update_data and isinstance(update_data['date'], datetime.date):
                        update_data['date'] = update_data['date'].isoformat()

                    supabase.table("pitch_logs").update(update_data).eq("id", row['id']).execute()
                    
                st.success("データベースの変更を保存しました。")
                st.rerun()
            except Exception as e:
                st.error(f"保存中にエラーが起きました: {e}")
            
    else:
        st.info("データベースは空っぽです。最初の1球を入力してください。")