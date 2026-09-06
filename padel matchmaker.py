import json
import random

import pandas as pd
import streamlit as st
from streamlit_local_storage import LocalStorage


TOTAL_SCORE = 21
STORE_KEY = "padel-play-session"
st.set_page_config(page_title="Padel Play", page_icon="🎾", layout="centered")

st.markdown("""<style>
.stApp {background:#fbfaf6;color:#18251d}.block-container{max-width:760px;padding-top:1.2rem;padding-bottom:3rem}
.hero{background:linear-gradient(125deg,#163c2b,#287a4f 65%,#b6e64c);color:#fff;border-radius:24px;padding:24px;margin-bottom:18px}.hero h1{margin:0;color:#fff}
.court-card{background:#fff;border:1px solid #e7eadf;border-radius:18px;padding:18px;margin:12px 0}.team-a{color:#147a4c;font-weight:700}.team-b{color:#2465b0;font-weight:700}.small-label{color:#6d756e;font-size:.83rem;text-transform:uppercase}.stButton>button{border-radius:12px;font-weight:700;min-height:44px}
</style>""", unsafe_allow_html=True)


def default_state():
    return {"screen": "setup", "players": {}, "round": 1, "active_round": [], "courts": 1,
            "meeting_target": 1, "meetings": {}, "history": [], "pending_scores": {}, "event_name": "Padel Play"}


storage = LocalStorage()


def load_saved():
    raw = storage.getItem(STORE_KEY)
    try:
        saved = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(saved, dict) or "meeting_target" not in saved:
        return None
    result = default_state()
    result.update(saved)
    return result


if "padel" not in st.session_state:
    st.session_state.padel = load_saved() or default_state()


def state():
    return st.session_state.padel


def persist():
    storage.setItem(STORE_KEY, json.dumps(state(), ensure_ascii=False))


def reset():
    st.session_state.padel = default_state()
    storage.eraseItem(STORE_KEY)


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
    st.subheader("Mulai sesi baru")
    st.caption("Masukkan pemain, jumlah lapangan, dan berapa kali setiap pemain perlu bertemu pemain lain.")
    name = st.text_input("Nama sesi", value=state()["event_name"])
    names_text = st.text_area("Daftar pemain", placeholder="Satu nama per baris\nAlya\nBima\nCitra", height=190)
    left, right = st.columns(2)
    with left:
        courts = st.selectbox("Lapangan aktif", [1, 2, 3])
    with right:
    target_games = st.number_input(
        "Target main per pemain",
        min_value=1,
        max_value=10,
        value=3,
        help="Sistem akan berusaha membuat setiap pemain bermain sebanyak target ini dengan partner yang berbeda."
    )
    names, seen = [], set()
    for item in names_text.splitlines():
        item = item.strip()
        if item and item.casefold() not in seen:
            names.append(item)
            seen.add(item.casefold())
    st.info(f"{len(names)} pemain terdeteksi · maksimal {courts * 4} pemain bermain per ronde")
    if len(names) < 4:
        st.warning("Butuh minimal 4 pemain untuk memulai.")
    elif st.button("Mulai & acak ronde pertama", type="primary", use_container_width=True):
        s = state()
        s.update({"event_name": name.strip() or "Padel Play", "players": {p: record() for p in names}, "courts": courts, "meeting_target": 1, "target_games": int(target_games), "meetings": {}, "round": 1, "screen": "playing", "history": [], "pending_scores": {}})
        choose_round()
        persist()
        st.rerun()

elif state()["screen"] == "playing":
    s, total = state(), len(state()["players"])
    playing = len(s["active_round"]) * 4

    a, b, c = st.columns(3)
    a.metric("Ronde", s["round"])
    b.metric("Main sekarang", f"{playing}/{total}")
    c.metric("Istirahat", total - playing)

    st.subheader(f"Ronde {s['round']} · pasangan sudah diacak")

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

        left, right = st.columns(2)

        with left:
            st.markdown(
                f"""
                <div class='court-card'>
                    <div class='small-label'>Lapangan {court}</div>
                    <p class='team-a'>
                        🟢 {' & '.join(match['team_a'])}
                    </p>
                """,
                unsafe_allow_html=True
            )

            score_a = st.number_input(
                f"Skor hijau · L{court}",
                min_value=0,
                max_value=TOTAL_SCORE,
                key=a_key
            )

            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown(
                f"""
                <div class='court-card'>
                    <div class='small-label'>Lapangan {court}</div>
                    <p class='team-b'>
                        🔵 {' & '.join(match['team_b'])}
                    </p>
                """,
                unsafe_allow_html=True
            )

            score_b = st.number_input(
                f"Skor biru · L{court}",
                min_value=0,
                max_value=TOTAL_SCORE,
                key=b_key
            )

            st.markdown("</div>", unsafe_allow_html=True)

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
    st.dataframe(standings(), use_container_width=True)

    with st.expander("Pengaturan sesi"):
        st.warning(
            "Jika pertandingan diakhiri, seluruh data sesi saat ini "
            "akan dihapus dan kamu harus memasukkan nama pemain lagi."
        )

        if st.button(
            "Akhiri pertandingan & mulai sesi baru",
            type="secondary",
            use_container_width=True
        ):
            reset()
            st.rerun()


else:
    st.balloons()
    st.subheader("🏆 Sesi selesai!")

    table = standings()

    if not table.empty:
        st.success(
            f"Juara hari ini: **{table.iloc[0]['Pemain']}** — selamat! 🎉"
        )
        st.dataframe(table, use_container_width=True)

    if st.button(
        "Buat sesi baru",
        type="primary",
        use_container_width=True
    ):
        reset()
        st.rerun()
