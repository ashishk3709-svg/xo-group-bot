import os, uuid, random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import InputMediaPhoto
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters


def td_pools():
    topics = [
        "your biggest secret", "your crush", "your last awkward moment",
        "your biggest fear", "your friendship circle", "your first impression",
        "your most embarrassing moment", "your biggest regret", "your jealousy",
        "your dream partner", "your trust issues", "your funniest lie",
        "your hidden talent", "your biggest insecurity", "your social life",
        "your online personality", "your worst habit", "your best quality",
        "your most awkward conversation", "your dream date", "your loyalty",
        "your biggest misunderstanding", "your secret ambition", "your confidence",
        "your biggest disappointment", "your favourite person", "your school drama",
        "your funniest memory", "your friendship standards", "your ideal weekend",
        "your biggest motivation", "your personal boundaries", "your first impression of this group",
        "your most unexpected compliment", "your biggest achievement", "your dream lifestyle",
        "your biggest temptation", "your funniest excuse", "your communication style",
        "your most controversial opinion", "your dream vacation", "your biggest challenge",
        "your definition of love", "your biggest lesson", "your future goals",
        "your favourite memory", "your competitive side", "your sense of humour",
        "your secret ambition", "your perfect day"
    ]

    tf = [
        "What's the most unexpected thing about {}?",
        "What's one thing you'd never admit about {}?",
        "Have you ever lied about {}?",
        "What's your most honest opinion about {}?",
        "What's the biggest lesson you've learned about {}?",
        "What's the funniest incident involving {}?",
        "What's one thing you'd change about {}?",
        "What's your biggest red flag related to {}?",
        "What's something people don't know about {}?",
        "What's the boldest decision you've made about {}?"
    ]

    df = [
        "Describe {} in three brutally honest words.",
        "Make a dramatic announcement about {} in the group.",
        "Give {} a hilarious new nickname.",
        "Write a one-line confession about {}.",
        "Explain {} like you're in a movie trailer.",
        "Create a funny headline about {}.",
        "Describe {} using only three emojis.",
        "Give a 10-second speech about {}.",
        "Make a funny fake award for {}.",
        "Turn {} into a dramatic movie title."
    ]

    return (
        [f.format(t) for f in tf for t in topics],
        [f.format(t) for f in df for t in topics]
    )


games = {}
streaks = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌⭕ Tic-Tac-Toe", callback_data="select:ttt")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="select:rps")],
        [InlineKeyboardButton("🔢 Number Guessing Battle", callback_data="select:num")],
        [InlineKeyboardButton("🔢 2048 Duel", callback_data="select:2048")],
        [InlineKeyboardButton("🔥 Truth or Dare", callback_data="select:td")],
    ])

def join_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 JOIN GAME", callback_data="join")],
    ])

def rps_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✊ Rock", callback_data="rps:rock"),
         InlineKeyboardButton("✋ Paper", callback_data="rps:paper"),
         InlineKeyboardButton("✌️ Scissors", callback_data="rps:scissors")],
    ])

def board(g):
    rows = []
    for r in range(3):
        rows.append([
            InlineKeyboardButton(
                g["b"][r*3+c] or "⬜",
                callback_data=f"move:{g['id']}:{r*3+c}"
            ) for c in range(3)
        ])
    return InlineKeyboardMarkup(rows)

def check(b):
    lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,c,d in lines:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    return "DRAW" if all(b) else None

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Add XO to a group to play!")
        return
    if chat.id in games:
        await update.message.reply_text("A match is already active in this group!")
        return

    g = {
        "id": uuid.uuid4().hex[:8],
        "creator": update.effective_user.id,
        "chat": chat.id
    }
    games[chat.id] = g
    msg = await update.message.reply_text(
        "🎮 XO GAME ARENA\n\nWhich game do you want to play?",
        reply_markup=menu()
    )
    g["message"] = msg.message_id


def render_ludo_poster(g):
    W = H = 800
    img = Image.new("RGB", (W, H), "#101827")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    colors = ["#ef4444", "#22c55e", "#eab308", "#3b82f6"]
    names = ["RED", "GREEN", "YELLOW", "BLUE"]

    d.rounded_rectangle((18, 18, 782, 782), radius=35, fill="#f8fafc")
    d.text((400, 42), "LUDO MINI ARENA", fill="#172554", anchor="mm", font=font)
    d.text((400, 72), "LIVE GAME BOARD", fill="#475569", anchor="mm", font=font)

    # Four player home areas
    homes = [(45, 115, 245, 285), (555, 115, 755, 285),
             (45, 515, 245, 685), (555, 515, 755, 685)]
    home_centres = [(145, 200), (655, 200), (145, 600), (655, 600)]

    for i, (x1, y1, x2, y2) in enumerate(homes):
        d.rounded_rectangle((x1, y1, x2, y2), radius=22,
                            fill=colors[i], outline="#1e293b", width=4)
        d.text(((x1+x2)//2, y1+22), names[i], fill="white",
               anchor="mm", font=font)
        for j in range(4):
            x = x1 + 55 + (j % 2) * 90
            y = y1 + 75 + (j // 2) * 65
            d.ellipse((x-19, y-19, x+19, y+19),
                      fill="#ffffff", outline="#1e293b", width=3)

    # Twenty spaces on a circular race track
    cx, cy, rx, ry = 400, 400, 220, 220
    coords = []
    for i in range(20):
        import math
        a = -math.pi/2 + 2*math.pi*i/20
        coords.append((cx + rx*math.cos(a), cy + ry*math.sin(a)))

    for i, (x, y) in enumerate(coords):
        r = 24
        fill = "#fde68a" if i in {0, 5, 10, 15} else "#e2e8f0"
        d.ellipse((x-r, y-r, x+r, y+r), fill=fill,
                  outline="#334155", width=3)
        d.text((x, y), str(i), fill="#0f172a", anchor="mm", font=font)

    d.ellipse((325, 325, 475, 475), fill="#172554", outline="#0f172a", width=5)
    d.text((400, 375), "FINISH", fill="white", anchor="mm", font=font)
    d.text((400, 420), "🏁", fill="white", anchor="mm", font=font)

    players = g.get("players", [])
    positions = g.get("positions", {})
    for pi, uid in enumerate(players):
        col = colors[pi % 4]
        for ti, pos in enumerate(positions.get(uid, [-1]*4)):
            if pos == -1:
                hx, hy = home_centres[pi % 4]
                x = hx + (-25 if ti % 2 == 0 else 25)
                y = hy + (-20 if ti < 2 else 20)
            elif pos >= 20:
                x = 400 + (ti % 2 * 24 - 12)
                y = 400 + (ti // 2 * 24 - 12)
            else:
                x, y = coords[pos]
                x += (ti % 2 * 13 - 6)
                y += (ti // 2 * 13 - 6)
            d.ellipse((x-13, y-13, x+13, y+13),
                      fill=col, outline="#111827", width=3)
            d.text((x, y), str(ti+1), fill="white",
                   anchor="mm", font=font)

    # Player legend
    for i, uid in enumerate(players):
        y = 720 + (i//2)*22
        x = 75 + (i%2)*350
        d.ellipse((x, y-7, x+14, y+7), fill=colors[i % 4])
        d.text((x+22, y), str(g["names"].get(uid, "Player"))[:24],
               fill="#0f172a", anchor="lm", font=font)

    out = BytesIO()
    img.save(out, format="PNG")
    out.name = "ludo_board.png"
    out.seek(0)
    return out


async def show_ludo(q, g, caption, keyboard=None):
    poster = render_ludo_poster(g)
    if q.message.photo:
        await q.edit_message_media(
            media=InputMediaPhoto(media=poster, caption=caption),
            reply_markup=keyboard
        )
    else:
        await q.message.delete()
        await q.message.get_bot().send_photo(
            chat_id=q.message.chat_id, photo=poster,
            caption=caption, reply_markup=keyboard
        )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not (q.data in ("ludojoin", "ludostart", "ludoroll") or q.data.startswith("ludomove:")):
        await q.answer()
    chat = q.message.chat_id
    g = games.get(chat)
    uid = q.from_user.id
    name = q.from_user.first_name


    if q.data.startswith("td:"):
        if not g or g.get("type") != "td":
            await q.answer("No active Truth or Dare game.", show_alert=True)
            return
        action=q.data.split(":")[1]
        players=g["td_players"]

        if action == "join":
            if g["td_started"]:
                await q.answer("Game already started!", show_alert=True)
                return
            if uid in players:
                await q.answer("You already joined!")
                return
            players.append(uid)
            g["td_names"][uid]=name
            g["td_skips"][uid]=0
            await q.edit_message_text(
                "🔥 TRUTH OR DARE LOBBY 🔥\\n\\n"+
                "\\n".join(f"{i+1}. {g['td_names'][x]}" for i,x in enumerate(players))+
                "\\n\\nJoin before the creator starts!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🙋 JOIN",callback_data="td:join")],
                    [InlineKeyboardButton("▶️ START",callback_data="td:start")]
                ])
            )
            return

        if action == "start":
            if uid != g["creator"] or g["td_started"] or len(players)<2:
                await q.answer("Creator only. At least 2 players must join.",show_alert=True)
                return
            g["td_started"]=True
            g["td_turn"]=0
            await q.edit_message_text(
                f"🔥 TRUTH OR DARE STARTED!\\n\\n{g['td_names'][players[0]]}'s turn. Choose Truth or Dare.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💚 TRUTH",callback_data="td:truth"),
                     InlineKeyboardButton("❤️ DARE",callback_data="td:dare")]
                ])
            )
            return

        if not g["td_started"]:
            await q.answer("The creator must start the game first.",show_alert=True)
            return
        current=players[g["td_turn"]]
        if uid != current:
            await q.answer("Wait for your turn!",show_alert=True)
            return

        if action == "skip":
            if q.message.message_id != g.get("td_prompt_id"):
                await q.answer("This is not the current question.",show_alert=True)
                return
            if g["td_skips"][uid] >= 3:
                await q.answer("No skips left! This question is compulsory.",show_alert=True)
                return
            g["td_skips"][uid] += 1
            await q.edit_message_text("⏭️ Question skipped.")
            await context.bot.edit_message_text(
                chat_id=chat, message_id=g["td_panel_id"],
                text=f"🔥 {g['td_names'][uid]}'s turn\\nSkips left: {3-g['td_skips'][uid]}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💚 TRUTH",callback_data="td:truth"),
                     InlineKeyboardButton("❤️ DARE",callback_data="td:dare")]
                ])
            )
            return

        if action in ("truth","dare"):
            pool=g["td_"+action]
            if not pool:
                await q.answer("No prompts left in this category!",show_alert=True)
                return
            prompt=pool.pop(random.randrange(len(pool)))
            g["td_current_kind"]=action
            remaining=3-g["td_skips"][uid]
            kb=InlineKeyboardMarkup([[InlineKeyboardButton(
                f"⏭️ SKIP ({remaining} left)",callback_data="td:skip"
            )]]) if remaining else None
            await context.bot.edit_message_text(
                chat_id=chat, message_id=g["td_panel_id"],
                text=f"🔥 {action.upper()} — {g['td_names'][uid]}'s turn\n\n{prompt}\n\nReply directly to THIS message with your answer."+
                     ("\n⏭️ You may skip this question." if remaining else "\n🔒 No skips left. Answer is compulsory."),
                reply_markup=kb
            )
            g["td_prompt_id"]=g["td_panel_id"]
            return
        return

    if q.data.startswith("select:"):
        if not g or uid != g["creator"] or g.get("type"):
            await q.answer("This game selection is unavailable.", show_alert=True)
            return

        if q.data == "select:ttt":
            g.update({
                "type": "ttt", "b": [""]*9,
                "x": None, "o": None, "turn": None, "names": {}
            })
            text = "❌⭕ TIC-TAC-TOE\n\nA new match is open!\nPress JOIN GAME."
        elif q.data == "select:rps":
            g.update({
                "type": "rps_setup", "p1": None, "p2": None,
                "choices": {}, "names": {}
            })
            text = "✊ ROCK PAPER SCISSORS\n\nChoose points to win:"
        elif q.data == "select:ludo":
            g.update({"type": "ludo", "players": [], "positions": {}, "names": {}, "turn": 0, "roll": None})
            text = "🎲 LUDO MINI\n\n2–4 players can join. Four tokens each. Join and wait for the creator to start!"

        elif q.data == "select:td":
            truths,dares=td_pools()
            random.shuffle(truths)
            random.shuffle(dares)
            g.update({"type":"td","td_truth":truths,"td_dare":dares,
                      "td_players":[],"td_names":{},"td_skips":{},
                      "td_started":False,"td_panel_id":q.message.message_id})
            text="🔥 TRUTH OR DARE 🔥\\n\\nJoin the competition!\\nEach player gets 3 skips. Reply to your exact question when it's your turn."
        elif q.data == "select:2048":
            b = [[0]*4 for _ in range(4)]
            for _ in range(2):
                r,c = random.choice([(r,c) for r in range(4) for c in range(4) if not b[r][c]])
                b[r][c] = 2
            g.update({"type":"2048","owner":uid,"board":b,"score":0})
            text = "🔢 2048 SINGLE PLAYER\n\n" + "\\n".join(" ".join(str(x or '⬜') for x in row) for row in b) + "\\n\\nScore: 0"
        else:
            g.update({
                "type": "number", "p1": None, "p2": None,
                "turn": None, "secret": None, "names": {}
            })
            text = "🔢 NUMBER GUESSING BATTLE\n\nJoin the game and guess the secret number from 1 to 10!"
        if g["type"] == "rps_setup":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("1 Point", callback_data="rpspoints:1"),
                 InlineKeyboardButton("3 Points", callback_data="rpspoints:3")],
                [InlineKeyboardButton("5 Points", callback_data="rpspoints:5"),
                 InlineKeyboardButton("10 Points", callback_data="rpspoints:10")]
            ])
        elif g["type"] == "number":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 JOIN GAME", callback_data="numjoin")]
            ])
        elif g["type"] == "ludo":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 JOIN LUDO", callback_data="ludojoin")],
                [InlineKeyboardButton("▶️ START MATCH", callback_data="ludostart")]
            ])

        elif g["type"] == "td":
            keyboard=InlineKeyboardMarkup([
                [InlineKeyboardButton("🙋 JOIN",callback_data="td:join")],
                [InlineKeyboardButton("▶️ START",callback_data="td:start")]
            ])
        elif g["type"] == "2048":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬆️", callback_data="2048:up")],
                [InlineKeyboardButton("⬅️", callback_data="2048:left"),
                 InlineKeyboardButton("⬇️", callback_data="2048:down"),
                 InlineKeyboardButton("➡️", callback_data="2048:right")],
                [InlineKeyboardButton("🔄 RESTART", callback_data="2048:restart")]
            ])
        else:
            keyboard = join_menu()
        await q.edit_message_text(text, reply_markup=keyboard)
        return

    if q.data.startswith("rpspoints:"):
        if not g or g.get("type") != "rps_setup" or uid != g["creator"]:
            await q.answer("Only the match creator can choose points.", show_alert=True)
            return
        g["target"] = int(q.data.split(":")[1])
        g["type"] = "rps"
        await q.edit_message_text(
            f"✊ ROCK PAPER SCISSORS\n\nFirst to {g['target']} point(s) wins!\n\nWaiting for two players...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 JOIN GAME", callback_data="rpsjoin")]
            ])
        )
        return

    if q.data == "rpsjoin":
        if not g or g.get("type") != "rps":
            await q.answer("No Rock Paper Scissors lobby.", show_alert=True)
            return
        if g["p1"] is None:
            g["p1"] = uid
            g["names"][uid] = name
            await q.edit_message_text(
                f"✊ ROCK PAPER SCISSORS\n\n{name} joined!\nWaiting for Player 2...",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 JOIN GAME", callback_data="rpsjoin")]])
            )
            return
        if g["p1"] == uid:
            await q.answer("Waiting for another player!", show_alert=True)
            return
        if g["p2"] is not None:
            await q.answer("Match is full!", show_alert=True)
            return

        g["p2"] = uid
        g["names"][uid] = name
        await q.edit_message_text(
            f"✊ ROCK PAPER SCISSORS MATCH STARTED!\n\n"
            f"👤 {g['names'][g['p1']]}\n👤 {name}\n\n"
            "Both players: choose secretly!",
            reply_markup=rps_menu()
        )
        return

    if q.data.startswith("rps:"):
        if not g or g.get("type") != "rps":
            await q.answer("Match ended!", show_alert=True)
            return
        if uid not in (g["p1"], g["p2"]):
            await q.answer("You are not playing in this match!", show_alert=True)
            return
        if uid in g["choices"]:
            await q.answer("Your choice is already locked!", show_alert=True)
            return

        choice = q.data.split(":")[1]
        g["choices"][uid] = choice

        if len(g["choices"]) == 1:
            return

        a, b = g["p1"], g["p2"]
        ca, cb = g["choices"][a], g["choices"][b]
        labels = {"rock": "✊ Rock", "paper": "✋ Paper", "scissors": "✌️ Scissors"}

        if ca == cb:
            result = "🤝 ROUND DRAW! No points awarded."
        else:
            wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
            winner = a if wins[ca] == cb else b
            loser = b if winner == a else a
            g.setdefault("scores", {a: 0, b: 0})
            g["scores"][winner] += 1
            result = f"🏆 {g['names'][winner]} wins this round!"

        score = g.setdefault("scores", {a: 0, b: 0})
        scoreboard = (
            f"📊 SCORE\n{g['names'][a]}: {score[a]} - "
            f"{g['names'][b]}: {score[b]}\n"
        )

        if score[a] >= g["target"] or score[b] >= g["target"]:
            match_winner = a if score[a] >= g["target"] else b
            match_loser = b if match_winner == a else a
            streaks[match_winner] = streaks.get(match_winner, 0) + 1
            streaks[match_loser] = 0
            result += (
                f"\n\n🏆 MATCH WINNER: {g['names'][match_winner]}!"
                f"\n🔥 Winning streak: {streaks[match_winner]}"
                f"\n💔 {g['names'][match_loser]} streak: 0"
            )
            games.pop(chat, None)
            await q.edit_message_text(
                f"✊ ROCK PAPER SCISSORS - FINAL RESULT\n\n"
                f"👤 {g['names'][a]}: {labels[ca]}\n"
                f"👤 {g['names'][b]}: {labels[cb]}\n\n"
                f"{result}\n{scoreboard}\nPlay again with /play"
            )
            return

        g["choices"] = {}
        await q.edit_message_text(
            f"✊ ROCK PAPER SCISSORS - ROUND RESULT\n\n"
            f"👤 {g['names'][a]}: {labels[ca]}\n"
            f"👤 {g['names'][b]}: {labels[cb]}\n\n"
            f"{result}\n{scoreboard}\nNext round: choose!",
            reply_markup=rps_menu()
        )
        return



    if q.data == "ludojoin":
        if not g or g.get("type") != "ludo":
            await q.answer("No active Ludo game.", show_alert=True)
            return
        if uid in g["players"]:
            await q.answer("Already joined!", show_alert=True)
            return
        if len(g["players"]) >= 4:
            await q.answer("Ludo is full!", show_alert=True)
            return
        await q.answer()
        g["players"].append(uid)
        g["names"][uid] = name
        g["positions"][uid] = [-1, -1, -1, -1]
        roster = "\n".join(f"{i+1}. {g['names'][u]}" for i, u in enumerate(g["players"]))
        await show_ludo(
            q, g,
            "🎲 LUDO MINI — PLAYERS JOINED\n\n" + roster +
            "\n\nNeed at least 2 players. Creator can start.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 JOIN LUDO", callback_data="ludojoin")],
                [InlineKeyboardButton("▶️ START MATCH", callback_data="ludostart")]
            ])
        )
        return

    if q.data == "ludostart":
        if not g or g.get("type") != "ludo" or uid != g["creator"]:
            await q.answer("Only creator can start.", show_alert=True)
            return
        if len(g["players"]) < 2:
            await q.answer("Need at least 2 players.", show_alert=True)
            return
        await q.answer()
        g["turn"] = 0
        player = g["players"][0]
        await show_ludo(
            q, g, f"🎲 LUDO MINI STARTED!\n\n{g['names'][player]}'s turn.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 ROLL DICE", callback_data="ludoroll")]
            ])
        )
        return

    if q.data == "ludoroll":
        if not g or g.get("type") != "ludo":
            await q.answer("No active Ludo game.", show_alert=True)
            return
        player = g["players"][g["turn"]]
        if uid != player:
            await q.answer("Wait for your turn!", show_alert=True)
            return
        if g["roll"] is not None:
            await q.answer("Choose a token first!", show_alert=True)
            return
        await q.answer()
        roll = random.randint(1, 6)
        g["roll"] = roll
        movable = [i for i, pos in enumerate(g["positions"][player])
                   if pos < 20 and (pos >= 0 or roll == 6)]
        if not movable:
            g["roll"] = None
            g["turn"] = (g["turn"] + 1) % len(g["players"])
            nxt = g["players"][g["turn"]]
            await show_ludo(
                q, g, f"🎲 {g['names'][player]} rolled {roll}. No move!\n\n{g['names'][nxt]}'s turn.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎲 ROLL DICE", callback_data="ludoroll")]
                ])
            )
            return
        await show_ludo(
            q, g, f"🎲 {g['names'][player]} rolled {roll}. Choose a token:",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Token {i+1}", callback_data=f"ludomove:{i}")]
                for i in movable
            ])
        )
        return

    if q.data.startswith("ludomove:"):
        if not g or g.get("type") != "ludo" or g.get("roll") is None:
            await q.answer("No active Ludo move.", show_alert=True)
            return
        player = g["players"][g["turn"]]
        if uid != player:
            await q.answer("Not your turn!", show_alert=True)
            return
        token = int(q.data.split(":")[1])
        positions = g["positions"][player]
        roll = g["roll"]
        if token not in range(4) or positions[token] >= 20 or (positions[token] == -1 and roll != 6):
            await q.answer("Invalid token.", show_alert=True)
            return
        await q.answer()
        positions[token] = 0 if positions[token] == -1 else min(20, positions[token] + roll)
        landed = positions[token]
        captured = []
        if landed < 20 and landed not in {0, 5, 10, 15}:
            for opponent in g["players"]:
                if opponent != player:
                    for i, pos in enumerate(g["positions"][opponent]):
                        if pos == landed:
                            g["positions"][opponent][i] = -1
                            captured.append(g["names"][opponent])
        g["roll"] = None
        if all(pos == 20 for pos in positions):
            streaks[player] = streaks.get(player, 0) + 1
            for opponent in g["players"]:
                if opponent != player:
                    streaks[opponent] = 0
            games.pop(chat, None)
            await show_ludo(
                q, g,
                f"🏆 LUDO FINISHED!\n\nWinner: {g['names'][player]}!\n🔥 Winning streak: {streaks[player]}",
                None
            )
            return
        if roll != 6:
            g["turn"] = (g["turn"] + 1) % len(g["players"])
        nxt = g["players"][g["turn"]]
        status = "\n".join(
            f"{g['names'][u]}: " + " | ".join(
                "🏁" if x == 20 else "🏠" if x == -1 else str(x)
                for x in g["positions"][u]
            ) for u in g["players"]
        )
        extra = "\n🎯 Captured: " + ", ".join(captured) if captured else ""
        await show_ludo(
            q, g,
            f"🎲 LUDO MINI\n\n{status}{extra}\n\n➡️ {g['names'][nxt]}'s turn!",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 ROLL DICE", callback_data="ludoroll")]
            ])
        )
        return

    if q.data.startswith("2048:"):
        if not g or g.get("type") != "2048":
            return
        if uid != g["owner"]:
            return
        direction = q.data.split(":")[1]
        if direction == "restart":
            b = [[0]*4 for _ in range(4)]
            for _ in range(2):
                r,c = random.choice([(r,c) for r in range(4) for c in range(4) if not b[r][c]])
                b[r][c] = 2
            g.update({"board":b,"score":0})
        else:
            b = g["board"]
            old = [row[:] for row in b]
            def compress(line):
                vals = [x for x in line if x]
                out, gained, i = [], 0, 0
                while i < len(vals):
                    if i+1 < len(vals) and vals[i] == vals[i+1]:
                        v = vals[i]*2
                        out.append(v)
                        gained += v
                        i += 2
                    else:
                        out.append(vals[i])
                        i += 1
                return out + [0]*(4-len(out)), gained
            if direction in ("left","right"):
                for r in range(4):
                    line = b[r][:] if direction == "left" else b[r][::-1]
                    new,gain = compress(line)
                    b[r] = new if direction == "left" else new[::-1]
                    g["score"] += gain
            else:
                for c in range(4):
                    line = [b[r][c] for r in range(4)]
                    if direction == "down":
                        line.reverse()
                    new,gain = compress(line)
                    if direction == "down":
                        new.reverse()
                    for r in range(4):
                        b[r][c] = new[r]
                    g["score"] += gain
            if b != old:
                empty = [(r,c) for r in range(4) for c in range(4) if not b[r][c]]
                if empty:
                    r,c = random.choice(empty)
                    b[r][c] = 4 if random.random() < .1 else 2
        won = any(2048 in row for row in g["board"])
        full = all(all(row) for row in g["board"])
        stuck = full and all(
            g["board"][r][c] != g["board"][r+1][c] and
            g["board"][r][c] != g["board"][r][c+1]
            for r in range(4) for c in range(4)
            if r < 3 and c < 3
        )
        status = "\\n🏆 YOU REACHED 2048!" if won else "\\n🏁 GAME OVER!" if stuck else ""
        await q.edit_message_text(
            "🔢 2048 SINGLE PLAYER\\n\\n" +
            "\\n".join(" ".join(str(x or '⬜') for x in row) for row in g["board"]) +
            f"\\n\\n⭐ Score: {g['score']}" + status,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬆️", callback_data="2048:up")],
                [InlineKeyboardButton("⬅️", callback_data="2048:left"),
                 InlineKeyboardButton("⬇️", callback_data="2048:down"),
                 InlineKeyboardButton("➡️", callback_data="2048:right")],
                [InlineKeyboardButton("🔄 RESTART", callback_data="2048:restart")]
            ])
        )
        return

    if q.data == "numjoin":
        if not g or g.get("type") != "number":
            return
        if g["p1"] is None:
            g["p1"] = uid
            g["names"][uid] = name
            await q.edit_message_text(
                f"🔢 NUMBER GUESSING BATTLE\n\n{name} joined!\nWaiting for Player 2...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎮 JOIN GAME", callback_data="numjoin")]
                ])
            )
            return
        if g["p1"] == uid or g["p2"] is not None:
            return
        g["p2"] = uid
        g["names"][uid] = name
        g["secret"] = random.randint(1, 10)
        g["turn"] = g["p1"]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(n), callback_data=f"numguess:{n}") for n in range(1, 6)],
            [InlineKeyboardButton(str(n), callback_data=f"numguess:{n}") for n in range(6, 11)]
        ])
        await q.edit_message_text(
            f"🔢 NUMBER GUESSING BATTLE STARTED!\n\n"
            f"👤 {g['names'][g['p1']]}\n👤 {g['names'][g['p2']]}\n\n"
            f"🎯 {g['names'][g['turn']]}: Guess the number (1–10)!",
            reply_markup=keyboard
        )
        return

    if q.data.startswith("numguess:"):
        if not g or g.get("type") != "number" or g.get("p2") is None:
            return
        if uid != g["turn"]:
            return
        guess = int(q.data.split(":")[1])
        if guess == g["secret"]:
            winner = uid
            loser = g["p2"] if uid == g["p1"] else g["p1"]
            streaks[winner] = streaks.get(winner, 0) + 1
            streaks[loser] = 0
            games.pop(chat, None)
            await q.edit_message_text(
                f"🔢 NUMBER GUESSING BATTLE - RESULT\n\n"
                f"🎯 Secret number: {g['secret']}\n"
                f"🏆 Winner: {g['names'][winner]}!\n"
                f"🔥 Winning streak: {streaks[winner]}\n"
                f"💔 {g['names'][loser]} streak: 0\n\n"
                f"Play again with /play"
            )
            return

        hint = "Higher! ⬆️" if guess < g["secret"] else "Lower! ⬇️"
        g["turn"] = g["p2"] if uid == g["p1"] else g["p1"]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(n), callback_data=f"numguess:{n}") for n in range(1, 6)],
            [InlineKeyboardButton(str(n), callback_data=f"numguess:{n}") for n in range(6, 11)]
        ])
        await q.edit_message_text(
            f"🔢 NUMBER GUESSING BATTLE\n\n"
            f"{g['names'][uid]} guessed {guess}.\n"
            f"{hint}\n\n"
            f"➡️ Next turn: {g['names'][g['turn']]}",
            reply_markup=keyboard
        )
        return

    if q.data == "join":
        if not g or g.get("type") != "ttt":
            await q.answer("No Tic-Tac-Toe lobby.", show_alert=True)
            return
        if not g:
            await q.answer("No open match.", show_alert=True)
            return
        if g["x"] is None:
            g["x"] = uid
            g["names"][uid] = name
            await q.edit_message_text(
                f"❌⭕ XO ARENA\n\n❌ {name} joined!\nWaiting for Player 2 ⭕...",
                reply_markup=join_menu()
            )
            return
        if g["x"] == uid:
            await q.answer("Waiting for another player!", show_alert=True)
            return
        if g["o"] is not None:
            await q.answer("Match is full!", show_alert=True)
            return

        g["o"] = uid
        g["names"][uid] = name
        g["turn"] = g["x"]
        await q.edit_message_text(
            f"🏆 MATCH STARTED!\n\n❌ {g['names'][g['x']]}\n⭕ {name}\n\n❌ YOUR TURN!",
            reply_markup=board(g)
        )
        return

    if q.data.startswith("move:"):
        if not g:
            await q.answer("Match ended!", show_alert=True)
            return
        _, gid, index = q.data.split(":")
        if gid != g["id"] or uid != g["turn"]:
            await q.answer("Not your turn!", show_alert=True)
            return
        index = int(index)
        if g["b"][index]:
            await q.answer("Square occupied!", show_alert=True)
            return

        mark = "❌" if uid == g["x"] else "⭕"
        g["b"][index] = mark
        win = check(g["b"])

        if win:
            if win == "DRAW":
                result = "🤝 IT'S A DRAW!"
            else:
                winner_id = uid
                loser_id = g["o"] if uid == g["x"] else g["x"]
                streaks[winner_id] = streaks.get(winner_id, 0) + 1
                streaks[loser_id] = 0
                result = (
                    f"🏆 {g['names'][winner_id]} WINS!\n"
                    f"🔥 Winning streak: {streaks[winner_id]}\n"
                    f"💔 {g['names'][loser_id]} streak: 0"
                )
            games.pop(chat, None)
            await q.edit_message_text(
                f"🎮 XO MATCH FINISHED\n\n{result}\n\nStart another match with /play"
            )
            return

        g["turn"] = g["o"] if uid == g["x"] else g["x"]
        symbol = "❌" if g["turn"] == g["x"] else "⭕"
        await q.edit_message_text(
            f"🎮 XO ARENA\n\n❌ {g['names'][g['x']]}\n⭕ {g['names'][g['o']]}\n\n{symbol} YOUR TURN!",
            reply_markup=board(g)
        )


async def td_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.reply_to_message or not msg.from_user:
        return

    chat = update.effective_chat.id
    g = games.get(chat)
    if not g or g.get("type") != "td" or not g.get("td_started"):
        return

    players = g["td_players"]
    if not players:
        return

    uid = msg.from_user.id
    prompt_id = g.get("td_prompt_id")

    if prompt_id is None or msg.reply_to_message.message_id != prompt_id:
        return
    if uid != players[g["td_turn"]]:
        return

    await context.bot.edit_message_reply_markup(
        chat_id=chat, message_id=prompt_id, reply_markup=None
    )

    g["td_prompt_id"] = None
    g["td_turn"] = (g["td_turn"] + 1) % len(players)
    nxt = players[g["td_turn"]]

    panel = await context.bot.send_message(
        chat_id=chat,
        text=f"✅ {g['td_names'][uid]} answered!\n\n"
             f"🔥 {g['td_names'][nxt]}'s turn. Choose Truth or Dare.\n"
             f"Skips left: {3-g['td_skips'][nxt]}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💚 TRUTH", callback_data="td:truth"),
             InlineKeyboardButton("❤️ DARE", callback_data="td:dare")]
        ])
    )
    g["td_panel_id"] = panel.message_id


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Use /end in the game group.")
        return

    g = games.get(chat.id)
    if not g:
        await update.message.reply_text("No active match to end.")
        return

    allowed = user.id in (
        g.get("creator"), g.get("x"), g.get("o"),
        g.get("p1"), g.get("p2")
    )

    if not allowed:
        member = await context.bot.get_chat_member(chat.id, user.id)
        allowed = member.status in ("administrator", "creator")

    if not allowed:
        await update.message.reply_text("Only the match creator, players, or group admins can end this match.")
        return

    games.pop(chat.id, None)
    await update.message.reply_text("🛑 MATCH ENDED!\n\nA new match can be started with /play.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 XO GAME ARENA\n\nAdd me to a group and use /play to choose a game!"
    )

def main():
    token = os.getenv("XO_TOKEN")
    if not token:
        raise RuntimeError("XO_TOKEN is missing!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("end", end_game))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, td_reply))
    app.add_handler(CallbackQueryHandler(buttons))
    print("XO GROUP BOT IS RUNNING!")
    app.run_polling()

if __name__ == "__main__":
    main()
