import os, uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

games = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 JOIN GAME", callback_data="join")],
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
        "id": uuid.uuid4().hex[:8], "b": [""]*9,
        "x": None, "o": None, "turn": None,
        "names": {}, "chat": chat.id
    }
    games[chat.id] = g
    msg = await update.message.reply_text(
        "❌⭕ XO ARENA\n\nA new match is open!\n\nPress JOIN GAME to participate.",
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

    if q.data == "join":
        if not g:
            await q.answer("No open match.", show_alert=True)
            return
        if g["x"] is None:
            g["x"] = uid
            g["names"][uid] = name
            await q.edit_message_text(
                f"❌⭕ XO ARENA\n\n❌ {name} joined!\nWaiting for Player 2 ⭕...",
                reply_markup=menu()
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
                result = f"🏆 {g['names'][uid]} WINS!"
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 XO ARENA\n\nAdd me to a group and use /play to start Tic-Tac-Toe!"
    )

def main():
    token = os.getenv("XO_TOKEN")
    if not token:
        raise RuntimeError("XO_TOKEN is missing!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CallbackQueryHandler(buttons))
    print("XO GROUP BOT IS RUNNING!")
    app.run_polling()

if __name__ == "__main__":
    main()
