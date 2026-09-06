import json
import random
from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Padel Play", page_icon="🎾", layout="centered")

st.markdown(
    """
    <style>
      .stApp { background: #fbfaf6; color: #18251d; }
      .block-container { max-width: 760px; padding-top: 1.2rem; padding-bottom: 3rem; }
      h1, h2, h3 { letter-spacing: -0.03em; }
      .hero { background: linear-gradient(125deg, #163c2b 0%, #287a4f 65%, #b6e64c 100%);
        color: white; border-radius: 24px; padding: 24px 24px 20px; margin-bottom: 18px; }
      .hero h1 { font-size: 2rem; margin: 0; color: white; }
      .hero p { margin: 5px 0 0; opacity: .86; }
      .court-card { background: white; border: 1px solid #e7eadf; border-radius: 18px;
        padding: 18px; margin: 12px 0; box-shadow: 0 5px 16px rgba(26, 58, 35, .05); }
      .team-a { color: #147a4c; font-weight: 700; } .team-b { color: #2465b0; font-weight: 700; }
      .small-label { color: #6d756e; font-size: .83rem; text-transform: uppercase; letter-spacing: .08em; }
      div[data-testid="stMetric"] { background: #fff; border: 1px solid #e7eadf; border-radius: 14px; padding: 10px; }
      .stButton > button { border-radius: 12px; font-weight: 700; min-height: 44px; }
      .stDownloadButton > button { border-radius: 12px; }
      [data-testid="stDataFrame"] { border: 1px solid #e7eadf; border-radius: 14px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def default_state():
    return {
        "screen": "setup",
        "players": {},
        "round": 1,
        "active_round": [],
        "courts": 1,
        "target_games": 5,
        "history": [],
        "event_name": "Padel Play",
    }


if "padel" not in st.session_state:
    st.session_state.padel = default_state()


def state():
    return st.session_state.padel


def player_record():
    return {"wins": 0, "diff": 0, "played": 0, "streak": 0, "partners": []}


def standings():
    rows = [
        {"Pemain": name, "Menang": d["wins"], "Selisih": d["diff"], "Main": d["played"]}
        for name, d in state()["players"].items()
    ]
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Menang", "Selisih", "Main", "Pemain"], ascending=[False, False, True, True]).reset_index(drop=True)
        df.index = df.index + 1
        df.index.name = "#"
    return df


def choose_round():
    """Choose players fairly: least games first, rest after two consecutive games, avoid repeat partners."""
    s = state()
    eligible = [p for p, d in s["players"].items() if d["played"] < s["target_games"]]
    slots = min(len(eligible) // 4, s["courts"]) * 4
    if slots < 4:
        s["screen"] = "finished"
        s["active_round"] = []
        return

    non_streak = [p for p in eligible if s["players"][p]["streak"] < 2]
    pool = non_streak if len(non_streak) >= slots else eligible
    random.shuffle(pool)
    pool.sort(key=lambda p: (s["players"][p]["played"], s["players"][p]["streak"]))
    selected = pool[:slots]

    # Greedy pairing: among the selected players, prefer someone who has not partnered before.
    remaining = selected[:]
    matches = []
    while remaining:
        first = remaining.pop(0)
        candidates = sorted(remaining, key=lambda p: (p in s["players"][first]["partners"], random.random()))
        partner = candidates[0]
        remaining.remove(partner)
        team_a = [first, partner]
        first = remaining.pop(0)
        candidates = sorted(remaining, key=lambda p: (p in s["players"][first]["partners"], random.random()))
        partner = candidates[0]
        remaining.remove(partner)
        matches.append({"team_a": team_a, "team_b": [first, partner]})
    s["active_round"] = matches


def reset_app():
    st.session_state.padel = default_state()


def save_round(scores):
    s = state()
    for match, (score_a, score_b) in zip(s["active_round"], scores):
        diff = score_a - score_b
        for team, won, value in ((match["team_a"], score_a > score_b, diff), (match["team_b"], score_b > score_a, -diff)):
            for p in team:
                d = s["players"][p]
                d["wins"] += int(won)
                d["diff"] += value
                d["played"] += 1
                d["streak"] += 1
            s["players"][team[0]]["partners"].append(team[1])
            s["players"][team[1]]["partners"].append(team[0])
        s["history"].append({"round": s["round"], "match": match, "score_a": score_a, "score_b": score_b})

    active_players = {p for m in s["active_round"] for team in (m["team_a"], m["team_b"]) for p in team}
    for p in s["players"]:
        if p not in active_players:
            s["players"][p]["streak"] = 0
    s["round"] += 1
    choose_round()


def backup_payload():
    return json.dumps(state(), ensure_ascii=False, indent=2)


st.markdown(f"""<div class="hero"><div class="small-label">Social Padel Manager</div>
<h1>🎾 {state()['event_name']}</h1><p>Putar pasangan. Catat skor. Biar semua kebagian main.</p></div>""", unsafe_allow_html=True)

if state()["screen"] == "setup":
    st.subheader("Mulai sesi baru")
    st.caption("Masukkan pemain, pilih jumlah lapangan, lalu aplikasi yang mengatur rotasinya.")
    event_name = st.text_input("Nama sesi", value=state()["event_name"], placeholder="Contoh: Jumat Night Padel")
    names_text = st.text_area("Daftar pemain", placeholder="Satu nama per baris\nAlya\nBima\nCitra", height=190)
    left, right = st.columns(2)
    with left:
        courts = st.selectbox("Lapangan aktif", [1, 2, 3], index=0)
    with right:
        target = st.number_input("Target main / orang", min_value=1, max_value=20, value=5)

    uploaded = st.file_uploader("Atau pulihkan sesi dari backup", type="json")
    if uploaded is not None:
        try:
            restored = json.load(uploaded)
            required = {"players", "round", "active_round", "courts", "target_games", "screen"}
            if required.issubset(restored):
                st.session_state.padel = restored
                st.success("Sesi berhasil dipulihkan.")
                st.rerun()
            else:
                st.error("File backup tidak sesuai format Padel Play.")
        except (json.JSONDecodeError, UnicodeDecodeError):
            st.error("Backup tidak bisa dibaca.")

    names = []
    seen = set()
    for raw in names_text.splitlines():
        name = raw.strip()
        key = name.casefold()
        if name and key not in seen:
            names.append(name)
            seen.add(key)
    capacity = courts * 4
    st.info(f"{len(names)} pemain terdeteksi · {capacity} pemain bermain per ronde")
    if names:
        st.caption(" · ".join(f"🎾 {n}" for n in names))
    if len(names) < capacity:
        st.warning(f"Butuh minimal {capacity} pemain untuk {courts} lapangan.")
    elif st.button("Mulai & acak ronde pertama", type="primary", use_container_width=True):
        s = state()
        s.update({"event_name": event_name.strip() or "Padel Play", "players": {n: player_record() for n in names}, "courts": courts, "target_games": target, "round": 1, "screen": "playing", "history": []})
        choose_round()
        st.rerun()

elif state()["screen"] == "playing":
    s = state()
    total = len(s["players"])
    playing = len(s["active_round"]) * 4
    a, b, c = st.columns(3)
    a.metric("Ronde", s["round"])
    b.metric("Main sekarang", f"{playing}/{total}")
    c.metric("Istirahat", total - playing)
    st.subheader(f"Ronde {s['round']} · pasangan sudah diacak")
    active = {p for m in s["active_round"] for team in (m["team_a"], m["team_b"]) for p in team}
    resting = [p for p in s["players"] if p not in active]
    if resting:
        st.caption("☕ Istirahat ronde ini: " + " · ".join(resting))

    scores = []
    for i, match in enumerate(s["active_round"], start=1):
        st.markdown(f'<div class="court-card"><div class="small-label">Lapangan {i}</div><p><span class="team-a">🟢 {" & ".join(match["team_a"])}</span><br><span class="team-b">🔵 {" & ".join(match["team_b"])}</span></p></div>', unsafe_allow_html=True)
        x, _, y = st.columns([1, .25, 1])
        with x:
            sa = st.number_input(f"Skor hijau · L{i}", 0, 99, 0, key=f"sa_{s['round']}_{i}")
        with y:
            sb = st.number_input(f"Skor biru · L{i}", 0, 99, 0, key=f"sb_{s['round']}_{i}")
        scores.append((sa, sb))

    if any(a == b for a, b in scores):
        st.warning("Skor seri tidak dapat disimpan. Tentukan satu pemenang di setiap lapangan.")
    elif st.button("Simpan skor & acak ronde berikutnya", type="primary", use_container_width=True):
        save_round(scores)
        st.rerun()

    st.divider()
    st.subheader("Klasemen live")
    st.dataframe(standings(), use_container_width=True)
    with st.expander("Pengaturan sesi"):
        st.download_button("Unduh backup sesi", backup_payload(), file_name=f"padel-play-{datetime.now():%Y%m%d-%H%M}.json", mime="application/json")
        if st.button("Akhiri sesi sekarang"):
            s["screen"] = "finished"
            st.rerun()
        if st.button("Reset sesi", type="secondary"):
            reset_app()
            st.rerun()

elif state()["screen"] == "finished":
    st.balloons()
    st.subheader("🏆 Sesi selesai!")
    table = standings()
    if not table.empty:
        champion = table.iloc[0]["Pemain"]
        st.success(f"Juara hari ini: **{champion}** — selamat! 🎉")
        st.dataframe(table, use_container_width=True)
    st.download_button("Unduh backup hasil", backup_payload(), file_name=f"hasil-padel-{datetime.now():%Y%m%d}.json", mime="application/json")
    if st.button("Buat sesi baru", type="primary", use_container_width=True):
        reset_app()
        st.rerun()
