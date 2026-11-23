from pathlib import Path
p=Path("bot.py")
s=p.read_text()

if 'callback_data="select:td"' in s:
    print("Truth or Dare menu already exists")
    raise SystemExit

s=s.replace(
    '[InlineKeyboardButton("🔢 2048 Duel", callback_data="select:2048")],',
    '[InlineKeyboardButton("🔢 2048 Duel", callback_data="select:2048")],\n        [InlineKeyboardButton("🔥 Truth or Dare", callback_data="select:td")],'
)

helper = '''
def td_pools():
    topics = [
        "school life","friendship","your childhood","your hobbies","your dreams",
        "your funniest memory","your favourite person","your personality",
        "your favourite game","your favourite movie","your favourite song",
        "your biggest achievement","your most awkward moment","your future",
        "your ideal friendship","your favourite food","your daily routine",
        "your secret talent","your favourite teacher","your best quality",
        "your worst habit","your dream holiday","your happiest day",
        "your biggest inspiration","your online life","your gaming life",
        "your school memories","your confidence","your biggest motivation",
        "your favourite sport","your favourite app","your perfect weekend",
        "your funniest nickname","your favourite season","your dream house",
        "your favourite celebration","your biggest lesson","your first impression",
        "your ideal relationship","your crush preferences","your definition of love",
        "your favourite cartoon","your favourite book","your dream adventure",
        "your best decision","your funniest chat","your childhood memories",
        "your favourite subject","your personal goals","your friendship secrets"
    ]
    tf = [
        "What is your funniest story about {}?",
        "What is one thing you would change about {}?",
        "What makes you happiest about {}?",
        "What is something people misunderstand about {}?",
        "What is your honest opinion about {}?",
        "What is your favourite memory of {}?",
        "What is one lesson you learned from {}?",
        "What would you improve about {}?",
        "What is the most surprising thing about {}?",
        "What is one thing you appreciate about {}?"
    ]
    df = [
        "Describe {} using exactly five words in this group.",
        "Make a two-line poem about {} and post it here.",
        "Explain {} using only emojis in this group.",
        "Write a funny headline about {} and share it here.",
        "Give {} a hilarious nickname and post it here.",
        "Make a mini-riddle about {} for the group.",
        "Write a dramatic one-line speech about {} here.",
        "Describe {} like a movie trailer in this group.",
        "Create a funny slogan about {} and post it here.",
        "Send a three-emoji story about {} in this group."
    ]
    return ([f.format(t) for f in tf for t in topics],
            [f.format(t) for f in df for t in topics])

'''

s=s.replace('games = {}\\nstreaks = {}','games = {}\\nstreaks = {}\\n'+helper)

s=s.replace('    if q.data.startswith("select:"):', '''
    if q.data.startswith("td:"):
        if not g or g.get("type") != "td":
            await q.answer("Start a new game with /play.", show_alert=True)
            return
        kind=q.data.split(":")[1]
        if kind == "skip":
            kind=g.get("td_current","truth")
        pool=g["td_"+kind]
        if not pool:
            await q.edit_message_text("🎉 All 500 prompts in this category are used! Start /play for a new game.")
            return
        prompt=pool.pop(random.randrange(len(pool)))
        g["td_current"]=kind
        await q.edit_message_text(
            f"🔥 TRUTH OR DARE 🔥\\\\n\\\\n👤 {name} chose {kind.upper()}!\\\\n\\\\n{prompt}\\\\n\\\\n"
            f"📦 {len(pool)} prompts remaining",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💚 TRUTH",callback_data="td:truth"),
                 InlineKeyboardButton("❤️ DARE",callback_data="td:dare")],
                [InlineKeyboardButton("⏭️ SKIP",callback_data="td:skip")]
            ])
        )
        return

    if q.data.startswith("select:"):''')

s=s.replace('        elif q.data == "select:2048":', '''
        elif q.data == "select:td":
            truths,dares=td_pools()
            random.shuffle(truths)
            random.shuffle(dares)
            g.update({"type":"td","td_truth":truths,"td_dare":dares})
            text="🔥 TRUTH OR DARE 🔥\\\\n\\\\n500 Truths + 500 Dares!\\\\nCrush, BF/GF, friendship and funny questions. Dares stay inside this Telegram group. You can skip any prompt."
        elif q.data == "select:2048":''')

s=s.replace('        elif g["type"] == "2048":', '''
        elif g["type"] == "td":
            keyboard=InlineKeyboardMarkup([
                [InlineKeyboardButton("💚 TRUTH",callback_data="td:truth"),
                 InlineKeyboardButton("❤️ DARE",callback_data="td:dare")]
            ])
        elif g["type"] == "2048":''')

p.write_text(s)
print("Patch applied")
