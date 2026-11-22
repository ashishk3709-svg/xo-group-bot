import os, uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

games = {}
streaks = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌⭕ Tic-Tac-Toe", callback_data="select:ttt")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="select:rps")],
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
        reply_markup=join_menu()
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
        else:
            g.update({
                "type": "rps", "p1": None, "p2": None,
                "choices": {}, "names": {}
            })
            text = "✊ ROCK PAPER SCISSORS\n\nA new match is open!\nTwo players can join."
        if g["type"] == "rps":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 JOIN GAME", callback_data="rpsjoin")]
            ])
        else:
            keyboard = join_menu()
        await q.edit_message_text(text, reply_markup=keyboard)
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
            result = "🤝 IT'S A DRAW!"
        else:
            wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
            winner = a if wins[ca] == cb else b
            loser = b if winner == a else a
            streaks[winner] = streaks.get(winner, 0) + 1
            streaks[loser] = 0
            result = (
                f"🏆 {g['names'][winner]} WINS!\n"
                f"🔥 Winning streak: {streaks[winner]}\n"
                f"💔 {g['names'][loser]} streak: 0"
            )

        games.pop(chat, None)
        await q.edit_message_text(
            f"✊ ROCK PAPER SCISSORS - RESULT\n\n"
            f"👤 {g['names'][a]}: {labels[ca]}\n"
            f"👤 {g['names'][b]}: {labels[cb]}\n\n"
            f"{result}\n\nPlay again with /play"
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
