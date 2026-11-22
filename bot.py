import os, uuid, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

games = {}
streaks = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌⭕ Tic-Tac-Toe", callback_data="select:ttt")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="select:rps")],
        [InlineKeyboardButton("🔢 Number Guessing Battle", callback_data="select:num")],
        [InlineKeyboardButton("🎲 Ludo Mini", callback_data="select:ludo")],
        [InlineKeyboardButton("🔢 2048 Duel", callback_data="select:2048")],
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

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat = q.message.chat_id
    g = games.get(chat)
    uid = q.from_user.id
    name = q.from_user.first_name

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
        elif q.data == "select:2048":
            g.update({"type": "2048_setup", "p1": None, "p2": None, "names": {}})
            text = "🔢 2048 DUEL\n\nTwo players compete on one shared board. Take turns sliding tiles!"
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
        elif g["type"] == "2048_setup":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 JOIN 2048", callback_data="2048join")]
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
            return
        if uid in g["players"]:
            await q.answer("Already joined!", show_alert=True)
            return
        if len(g["players"]) >= 4:
            await q.answer("Ludo is full!", show_alert=True)
            return
        g["players"].append(uid)
        g["names"][uid] = name
        g["positions"][uid] = [-1, -1, -1, -1]
        await q.edit_message_text(
            "🎲 LUDO MINI\n\n" +
            "\n".join(f"{i+1}. {g['names'][u]}" for i, u in enumerate(g["players"])) +
            "\n\nAt least 2 players needed. Creator can start.",
            reply_markup=InlineKeyboardMarkup([
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
        g["turn"] = 0
        player = g["players"][0]
        await q.edit_message_text(
            f"🎲 LUDO MINI STARTED!\n\n{g['names'][player]}'s turn.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 ROLL DICE", callback_data="ludoroll")]
            ])
        )
        return

    if q.data == "ludoroll":
        if not g or g.get("type") != "ludo":
            return
        player = g["players"][g["turn"]]
        if uid != player:
            await q.answer("Wait for your turn!", show_alert=True)
            return
        if g["roll"] is not None:
            await q.answer("Choose a token first!", show_alert=True)
            return
        import random
        roll = random.randint(1, 6)
        g["roll"] = roll
        movable = [i for i, pos in enumerate(g["positions"][player])
                   if pos < 20 and (pos >= 0 or roll == 6)]
        if not movable:
            g["roll"] = None
            g["turn"] = (g["turn"] + 1) % len(g["players"])
            nxt = g["players"][g["turn"]]
            await q.edit_message_text(
                f"🎲 {g['names'][player]} rolled {roll}. No move!\n\n{g['names'][nxt]}'s turn.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎲 ROLL DICE", callback_data="ludoroll")]
                ])
            )
            return
        await q.edit_message_text(
            f"🎲 {g['names'][player]} rolled {roll}. Choose token:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Token {i+1}", callback_data=f"ludomove:{i}")]
                for i in movable
            ])
        )
        return

    if q.data.startswith("ludomove:"):
        if not g or g.get("type") != "ludo" or g.get("roll") is None:
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
            await q.edit_message_text(
                f"🎲 LUDO FINISHED!\n\n🏆 Winner: {g['names'][player]}!\n"
                f"🔥 Winning streak: {streaks[player]}\n\nPlay again with /play"
            )
            return
        if roll != 6:
            g["turn"] = (g["turn"] + 1) % len(g["players"])
        nxt = g["players"][g["turn"]]
        status = "\n".join(
            f"{g['names'][u]}: " + " | ".join("🏁" if x == 20 else "🏠" if x == -1 else str(x) for x in g["positions"][u])
            for u in g["players"]
        )
        extra = "\n🎯 Captured: " + ", ".join(captured) if captured else ""
        await q.edit_message_text(
            f"🎲 LUDO MINI\n\n{status}{extra}\n\n➡️ {g['names'][nxt]}'s turn!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 ROLL DICE", callback_data="ludoroll")]
            ])
        )
        return

    if q.data == "2048join":
        if not g or g.get("type") != "2048_setup":
            return
        if uid == g["p1"] or uid == g["p2"]:
            return
        if g["p1"] is None:
            g["p1"] = uid
            g["names"][uid] = name
            await q.edit_message_text(
                f"🔢 2048 DUEL\n\n{name} joined! Waiting for Player 2...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎮 JOIN 2048", callback_data="2048join")]
                ])
            )
            return
        g["p2"] = uid
        g["names"][uid] = name
        import random
        b = [[0]*4 for _ in range(4)]
        for _ in range(2):
            r, c = random.choice([(r,c) for r in range(4) for c in range(4) if b[r][c] == 0])
            b[r][c] = 2
        g.update({"type": "2048", "board": b, "scores": {g["p1"]: 0, g["p2"]: 0}, "turn": g["p1"]})
        await q.edit_message_text(
            f"🔢 2048 DUEL STARTED!\n\n{g['names'][g['turn']]}'s turn.\n\n" +
            "\n".join(" ".join(str(x or "·") for x in row) for row in b),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬆️", callback_data="2048:up")],
                [InlineKeyboardButton("⬅️", callback_data="2048:left"),
                 InlineKeyboardButton("⬇️", callback_data="2048:down"),
                 InlineKeyboardButton("➡️", callback_data="2048:right")]
            ])
        )
        return

    if q.data.startswith("2048:"):
        if not g or g.get("type") != "2048":
            return
        if uid != g["turn"]:
            await q.answer("Wait for your turn!", show_alert=True)
            return
        direction = q.data.split(":")[1]
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

        gain_total = 0
        if direction in ("left", "right"):
            for r in range(4):
                line = b[r][:] if direction == "left" else b[r][::-1]
                new, gain = compress(line)
                b[r] = new if direction == "left" else new[::-1]
                gain_total += gain
        else:
            for c in range(4):
                line = [b[r][c] for r in range(4)]
                if direction == "down":
                    line.reverse()
                new, gain = compress(line)
                if direction == "down":
                    new.reverse()
                for r in range(4):
                    b[r][c] = new[r]
                gain_total += gain

        if b == old:
            await q.answer("No tiles moved that way!", show_alert=True)
            return
        g["scores"][uid] += gain_total
        import random
        empty = [(r,c) for r in range(4) for c in range(4) if b[r][c] == 0]
        if empty:
            r,c = random.choice(empty)
            b[r][c] = 4 if random.random() < .1 else 2
        if any(2048 in row for row in b):
            winner = uid
            loser = g["p2"] if uid == g["p1"] else g["p1"]
            streaks[winner] = streaks.get(winner, 0) + 1
            streaks[loser] = 0
            games.pop(chat, None)
            await q.edit_message_text(
                f"🔢 2048 DUEL FINISHED!\n\n🏆 {g['names'][winner]} reached 2048!\n"
                f"🔥 Winning streak: {streaks[winner]}\n\nPlay again with /play"
            )
            return
        g["turn"] = g["p2"] if uid == g["p1"] else g["p1"]
        await q.edit_message_text(
            "🔢 2048 DUEL\n\n" +
            "\n".join(" ".join(str(x or "·") for x in row) for row in b) +
            f"\n\n📊 {g['names'][g['p1']]}: {g['scores'][g['p1']]}"
            f"\n📊 {g['names'][g['p2']]}: {g['scores'][g['p2']]}"
            f"\n\n➡️ {g['names'][g['turn']]}'s turn!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬆️", callback_data="2048:up")],
                [InlineKeyboardButton("⬅️", callback_data="2048:left"),
                 InlineKeyboardButton("⬇️", callback_data="2048:down"),
                 InlineKeyboardButton("➡️", callback_data="2048:right")]
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
    app.add_handler(CallbackQueryHandler(buttons))
    print("XO GROUP BOT IS RUNNING!")
    app.run_polling()

if __name__ == "__main__":
    main()
