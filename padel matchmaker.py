import json
import random
import time

import pandas as pd
import streamlit as st
from streamlit_local_storage import LocalStorage


TOTAL_SCORE = 21
STORE_KEY = "padel-play-session"
st.set_page_config(page_title="Padel Play", page_icon="🎾", layout="centered")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=DM+Mono:wght@400;500;700&display=swap');
:root { --lime:#c7ff18; --ink:#080909; --panel:#0e0f10; --line:#292b2d; --muted:#777d83; }
.stApp { color:#f4f5ef; background:var(--ink); font-family:'DM Mono',monospace; }
.block-container { max-width:760px; padding:1.6rem 1.5rem 4rem; }
#MainMenu, footer, header { visibility:hidden; }
h1,h2,h3 { font-family:'Barlow Condensed',sans-serif !important; font-weight:800 !important; letter-spacing:.015em; color:#f9faf5 !important; }
.eyebrow,.field-label,.match-meta,.nav-copy { font-size:.63rem; letter-spacing:.13em; text-transform:uppercase; font-weight:700; }
.topbar { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); padding:0 0 1rem; margin-bottom:2.2rem; }
.brand { color:var(--lime); text-align:center; font-family:'Barlow Condensed',sans-serif; font-weight:800; font-size:.95rem; letter-spacing:.12em; line-height:1; }
.brand span { display:block; color:#797d81; font-family:'DM Mono',monospace; font-size:.53rem; letter-spacing:.1em; margin-top:.3rem; }
.nav-copy { color:#858a8e; min-width:92px; }.nav-copy.right { text-align:right; }
.setup-wrap { max-width:383px; margin:0 auto; padding-top:8vh; }
.setup-wrap h1 { font-size:3.15rem !important; line-height:.83; margin:.45rem 0 1.9rem; }
.eyebrow { color:var(--lime); }.field-label { color:#858a8e; margin-bottom:.45rem; }
.stTextInput input, [data-testid="stNumberInput"] input { background:#111214 !important; color:#f4f5ef !important; border:1px solid #2b2d30 !important; border-radius:4px !important; font-family:'DM Mono',monospace !important; font-weight:700; }
.stTextInput input { height:2.4rem; }
.player-count { color:#858a8e; font-size:.64rem; margin-bottom:.55rem; }
.player-chip { display:inline-block; background:#151618; border:1px solid #303236; color:#f7f8f2; padding:.28rem .55rem; border-radius:3px; margin:0 .35rem .4rem 0; font-size:.7rem; }
.player-chip b { color:#81868c; margin-left:.3rem; }
.stButton>button { min-height:2.35rem; border-radius:4px; border:1px solid #333538; background:#161719; color:#f6f7f1; font-family:'Barlow Condensed',sans-serif; font-size:.86rem; font-weight:800; letter-spacing:.08em; box-shadow:none; }
.stButton>button[kind="primary"] { background:var(--lime); color:#0a0b0b; border-color:var(--lime); }
.stButton>button:hover { border-color:var(--lime); color:var(--lime); }.stButton>button[kind="primary"]:hover { color:#080909; background:#d4ff4d; }
.main-title { font-size:1.65rem !important; margin:1.2rem 0 .7rem; }.round-head { display:flex; align-items:end; justify-content:space-between; margin:1.7rem 0 .7rem; border-bottom:1px solid var(--line); padding-bottom:.55rem; }
.round-head h2 { font-size:1.55rem !important; margin:0; }.match-meta { color:#7f858a; text-align:right; }
.match-card { display:grid; grid-template-columns:1fr auto auto auto 1fr; gap:.7rem; align-items:center; border:1px solid #2a2c2f; border-radius:4px; background:#0c0d0e; min-height:70px; padding:.8rem .9rem; margin-bottom:.7rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:#2a2c2f !important; background:#0c0d0e; border-radius:4px !important; margin-bottom:.7rem; }
.team {
    font-family:'Barlow Condensed',sans-serif;
    font-weight:800;
    font-size:1.05rem;
    line-height:1.05;
    position:relative;
    top:-10px;
}

.team-right {
    text-align:right;
}

.team span {
    display:block;
}

.team-a span:first-child,
.team-b span:first-child {
    color:#f8f9f3;
}

.team span:last-child {
    color:#72787e;
}
.score-separator { color:#54595d; font-weight:700; }.score-box { width:2.8rem; }.score-box [data-testid="stNumberInput"] { margin:0; }.score-box [data-testid="stNumberInput"] button { display:none; }.score-box input { text-align:center; height:2.25rem; padding:0 !important; }
.rest { color:#7f858a; font-size:.7rem; padding:.55rem .7rem; border-left:2px solid var(--lime); background:#101112; margin-bottom:1rem; }
.standings-wrap { padding-top:7vh; }.standings-wrap h1 { font-size:3rem !important; margin:.3rem 0 1.3rem; }
[data-testid="stDataFrame"] { border:1px solid #2a2c2f; border-radius:4px; overflow:hidden; }
[data-testid="stDataFrame"] * { font-family:'DM Mono',monospace !important; }
.winner { color:var(--lime); font-family:'Barlow Condensed',sans-serif; font-size:1.35rem; margin-bottom:1rem; }
@media (max-width:520px) { .block-container { padding-left:1rem; padding-right:1rem; } .match-card { gap:.38rem; padding:.7rem .55rem; } .team { font-size:.9rem; } .score-box { width:2.35rem; } }
</style>""", unsafe_allow_html=True)


def default_state():
    return {
        "screen": "setup",
        "players": {},
        "round": 1,
        "active_round": [],
        "courts": 1,
        "meeting_target": 1,
        "meetings": {},
        "history": [],
        "pending_scores": {},
        "event_name": "Padel Play"
    }


storage = LocalStorage()


def load_saved():
    raw = storage.getItem(STORE_KEY)

    if raw is None:
        return None

    try:
        saved = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(saved, dict):
        return None

    if not saved.get("players"):
        return None

    result = default_state()
    result.update(saved)

    return result


if "padel" not in st.session_state:

    saved_state = load_saved()

    if saved_state is not None:
        st.session_state.padel = saved_state
    else:
        st.session_state.padel = default_state()


def state():
    return st.session_state.padel


def persist():
    data = json.dumps(
        state(),
        ensure_ascii=False
    )

    storage.setItem(STORE_KEY, data)

    time.sleep(1.5)


def reset():
    st.session_state.padel = default_state()

    storage.eraseItem(STORE_KEY)

    time.sleep(1.0)

def add_draft_player():
    name = st.session_state.get("player_name", "").strip()
    draft = st.session_state.setdefault("draft_players", [])

    if (
        len(draft) < 16
        and name
        and name.casefold() not in {
            player.casefold() for player in draft
        }
    ):
        draft.append(name)

    st.session_state.player_name = ""


def record():
    return {"wins": 0, "diff": 0, "played": 0, "partners": []}


def pair_key(a, b):
    return "|".join(sorted((a, b), key=str.casefold))


def pair_count(a, b):
    return state()["meetings"].get(pair_key(a, b), 0)


def partner_count(a, b):
    """Berapa kali A dan B pernah menjadi partner."""
    count = 0

    for match in state()["history"]:
        team_a = match["match"]["team_a"]
        team_b = match["match"]["team_b"]

        if a in team_a and b in team_a:
            count += 1

        if a in team_b and b in team_b:
            count += 1

    return count


def opponent_count(a, b):
    """Berapa kali A dan B pernah menjadi lawan."""
    count = 0

    for match in state()["history"]:
        team_a = match["match"]["team_a"]
        team_b = match["match"]["team_b"]

        if (a in team_a and b in team_b) or (a in team_b and b in team_a):
            count += 1

    return count


def player_play_count(player):
    """Jumlah pertandingan yang sudah dimainkan pemain."""
    return state()["players"][player]["played"]


def all_partner_combinations_used():
    """True jika semua pasangan pemain sudah pernah menjadi partner."""
    people = list(state()["players"])

    for i, a in enumerate(people):
        for b in people[i + 1:]:
            if partner_count(a, b) == 0:
                return False

    return True


def choose_round():
    """
    Membuat ronde seadil mungkin.

    Prioritas:
    1. Pemain dengan jumlah pertandingan paling sedikit.
    2. Partner yang belum pernah dimainkan.
    3. Hindari lawan yang terlalu sering sama.
    4. Jika semua partner sudah pernah, mulai mengulang partner
       dengan jumlah pertemuan paling sedikit.
    """

    s = state()
    people = list(s["players"])

    max_slots = s["courts"] * 4

    if len(people) < 4:
        s["screen"] = "finished"
        s["active_round"] = []
        return

    # -----------------------------------------
    # PILIH PEMAIN YANG AKAN BERMAIN
    # -----------------------------------------

    # Cari jumlah pertandingan paling sedikit
    min_played = min(
        player_play_count(p)
        for p in people
    )

    # Pemain yang paling membutuhkan kesempatan bermain
    candidates = [
        p for p in people
        if player_play_count(p) == min_played
    ]

    # Tambahkan pemain berikutnya jika lapangan masih kosong
    remaining = [
        p for p in people
        if p not in candidates
    ]

    random.shuffle(candidates)
    random.shuffle(remaining)

    selected = candidates[:]

    # Isi slot sampai kapasitas lapangan
    while len(selected) < min(max_slots, len(people)) and remaining:

        # Pilih pemain dengan jumlah main paling sedikit
        best_player = min(
            remaining,
            key=lambda p: (
                player_play_count(p),
                sum(
                    partner_count(p, other)
                    for other in selected
                ),
                random.random()
            )
        )

        selected.append(best_player)
        remaining.remove(best_player)

    # Pastikan jumlah pemain kelipatan 4
    selected = selected[:(len(selected) // 4) * 4]

    if len(selected) < 4:
        s["screen"] = "finished"
        s["active_round"] = []
        return

    # -----------------------------------------
    # BUAT MATCH
    # -----------------------------------------

    matches = []

    while selected:

        # Ambil pemain pertama
        first = selected.pop(0)

        # Cari 3 pemain lain untuk membentuk 1 court
        group = [first]

        while len(group) < 4:

            def player_score(player):

                # Seberapa sering player menjadi partner
                # dengan anggota group
                partner_score = sum(
                    partner_count(player, teammate)
                    for teammate in group
                )

                # Seberapa sering player menjadi lawan
                # dengan anggota group
                opponent_score = sum(
                    opponent_count(player, teammate)
                    for teammate in group
                )

                # Prioritaskan partner yang belum pernah
                # menjadi partner
                new_partner_bonus = sum(
                    1
                    for teammate in group
                    if partner_count(player, teammate) == 0
                )

                return (
                    partner_score,
                    opponent_score,
                    -new_partner_bonus,
                    player_play_count(player),
                    random.random()
                )

            player = min(
                selected,
                key=player_score
            )

            group.append(player)
            selected.remove(player)

        a, b, c, d = group

        # -----------------------------------------
        # 3 KEMUNGKINAN KOMBINASI PARTNER
        # -----------------------------------------

        pairings = [
            ([a, b], [c, d]),
            ([a, c], [b, d]),
            ([a, d], [b, c]),
        ]

        def pairing_score(pairing):

            team_a, team_b = pairing

            # Partner score
            partner_score = (
                partner_count(*team_a)
                + partner_count(*team_b)
            )

            # Opponent score
            opponent_score = sum(
                opponent_count(player_a, player_b)
                for player_a in team_a
                for player_b in team_b
            )

            # Jumlah partner yang belum pernah
            new_partners = sum(
                1
                for team in pairing
                if partner_count(*team) == 0
            )

            return (
                partner_score,
                opponent_score,
                -new_partners,
                random.random()
            )

        # Pilih kombinasi paling adil
        best_pairing = min(
            pairings,
            key=pairing_score
        )

        team_a, team_b = best_pairing

        matches.append({
            "team_a": team_a,
            "team_b": team_b
        })

    s["active_round"] = matches


def standings():
    rows = [{"Pemain": name, "Menang": row["wins"], "Selisih": row["diff"], "Main": row["played"]} for name, row in state()["players"].items()]
    table = pd.DataFrame(rows)
    if not table.empty:
        table = table.sort_values(["Menang", "Selisih", "Main", "Pemain"], ascending=[False, False, True, True]).reset_index(drop=True)
        table.index, table.index.name = table.index + 1, "#"
    return table


def score_keys(court):
    return f"score_a_{state()['round']}_{court}", f"score_b_{state()['round']}_{court}"


def save_round(scores):
    s = state()
    for match, (score_a, score_b) in zip(s["active_round"], scores):
        people = match["team_a"] + match["team_b"]
        for i, a in enumerate(people):
            for b in people[i + 1:]:
                key = pair_key(a, b)
                s["meetings"][key] = s["meetings"].get(key, 0) + 1
        for team, won, difference in ((match["team_a"], score_a > score_b, score_a - score_b), (match["team_b"], score_b > score_a, score_b - score_a)):
            for player in team:
                s["players"][player]["wins"] += int(won)
                s["players"][player]["diff"] += difference
                s["players"][player]["played"] += 1
            s["players"][team[0]]["partners"].append(team[1])
            s["players"][team[1]]["partners"].append(team[0])
        s["history"].append({"round": s["round"], "match": match, "score_a": score_a, "score_b": score_b})
    s["round"] += 1
    s["pending_scores"] = {}
    choose_round()
    persist()


st.markdown(f"<div class='hero'><div class='small-label'>Social Padel Manager</div><h1>🎾 {state()['event_name']}</h1><p>Putar pasangan. Catat skor. Biar semua kebagian main.</p></div>", unsafe_allow_html=True)

if state()["screen"] == "setup":
    draft = st.session_state.setdefault("draft_players", [])

    st.markdown(
        "<div class='setup-wrap'>"
        "<div class='eyebrow'>Padel Americano</div>"
        "<h1>SETUP<br>TOURNAMENT</h1>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<div class='player-count'>"
        f"PLAYERS ({len(draft)}/16, MIN 4)"
        f"</div>",
        unsafe_allow_html=True
    )

    name_col, add_col = st.columns([5, 1])

    with name_col:
        st.text_input(
            "Player name",
            placeholder="Player name",
            key="player_name",
            label_visibility="collapsed",
            on_change=add_draft_player
        )

    with add_col:
        st.button(
            "Add",
            type="primary",
            use_container_width=True,
            on_click=add_draft_player
        )

    if draft:
        chips = "".join(
            f"<span class='player-chip'>{player}</span>"
            for player in draft
        )

        st.markdown(
            chips,
            unsafe_allow_html=True
        )

    st.selectbox(
        "Lapangan aktif",
        [1, 2, 3],
        key="setup_courts"
    )

    if len(draft) < 4:
        st.caption(
            "Tambahkan minimal 4 pemain untuk memulai."
        )
    elif len(draft) % 2 == 1:
        st.caption(
            "Jumlah pemain ganjil diperbolehkan. "
            "Sistem akan mengatur pemain yang istirahat secara otomatis."
        )

    can_start = len(draft) >= 4

    if st.button(
        "SHUFFLE & START",
        type="primary",
        use_container_width=True,
        disabled=not can_start
    ):
        s = state()

        s.update({
            "event_name": "Padel Play",
            "players": {
                p: record()
                for p in draft
            },
            "courts": st.session_state.setup_courts,
            "meeting_target": 1,
            "meetings": {},
            "round": 1,
            "screen": "playing",
            "history": [],
            "pending_scores": {}
        })

        choose_round()
        persist()
        st.rerun()

elif state()["screen"] == "playing":
    s, total = state(), len(state()["players"])
    playing = len(s["active_round"]) * 4

    st.markdown(
        "<div class='round-head'>"
        "<h2>PERTANDINGAN</h2>"
        "</div>",
        unsafe_allow_html=True
    )

    active = {
        p
        for match in s["active_round"]
        for team in (match["team_a"], match["team_b"])
        for p in team
    }

    rest = [p for p in s["players"] if p not in active]

    if rest:
        st.caption("☕ Istirahat ronde ini: " + " · ".join(rest))

    scores = []

    for court, match in enumerate(s["active_round"], 1):
        a_key, b_key = score_keys(court)
    
        initial = s["pending_scores"].get(
            str(court),
            [0, TOTAL_SCORE]
        )
    
        if a_key not in st.session_state:
            st.session_state[a_key] = initial[0]
    
        if b_key not in st.session_state:
            st.session_state[b_key] = initial[1]
    
        team_a = "".join(
            f"<span>{player}</span>"
            for player in match["team_a"]
        )
    
        team_b = "".join(
            f"<span>{player}</span>"
            for player in match["team_b"]
        )
    
        with st.container(border=True):
    
            card_left, score_a_col, dash, score_b_col, card_right = st.columns(
                [4.2, 1, .35, 1, 4.2]
            )
    
            with card_left:
                st.markdown(
                    f"<div class='team'>{team_a}</div>",
                    unsafe_allow_html=True
                )
    
            with score_a_col:
                score_a = st.number_input(
                    f"Team A score {court}",
                    0,
                    TOTAL_SCORE,
                    key=a_key,
                    label_visibility="collapsed"
                )
    
            with dash:
                st.markdown(
                    "<div class='score-separator'>—</div>",
                    unsafe_allow_html=True
                )
    
            with score_b_col:
                score_b = st.number_input(
                    f"Team B score {court}",
                    0,
                    TOTAL_SCORE,
                    key=b_key,
                    label_visibility="collapsed"
                )
    
            with card_right:
                st.markdown(
                    f"<div class='team team-right'>{team_b}</div>",
                    unsafe_allow_html=True
                )
    
        scores.append((score_a, score_b))


    invalid_scores = [
        (a, b)
        for a, b in scores
        if a + b != TOTAL_SCORE
    ]

    if invalid_scores:
        st.warning(
            f"Total skor setiap pertandingan harus {TOTAL_SCORE}. "
            "Contoh yang valid: 15–6."
        )


    if st.button(
        "Simpan skor & acak ronde berikutnya",
        type="primary",
        use_container_width=True
    ):
        if invalid_scores:
            st.error(
                f"Skor belum valid. Total skor setiap pertandingan harus {TOTAL_SCORE}."
            )
        else:
            save_round(scores)
            st.rerun()
        
    st.divider()
    st.subheader("Klasemen live")
    st.dataframe(
        standings(),
        use_container_width=True
    )

    if st.button(
        "GAME OVER",
        type="secondary",
        use_container_width=True
    ):
        s["screen"] = "finished"
        persist()
        st.rerun()


else:
    st.markdown(
        "<div class='standings-wrap'>"
        "<div class='eyebrow'>Tournament complete</div>"
        "<h1>STANDINGS</h1>"
        "</div>",
        unsafe_allow_html=True
    )

    table = standings()

    if not table.empty:
        st.markdown(
            f"<div class='winner'>"
            f"#1 {table.iloc[0]['Pemain']}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=False
        )

    if st.button(
        "NEW GAME",
        type="primary",
        use_container_width=True
    ):
        reset()
        st.session_state.draft_players = []
        st.rerun()
