import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, events, Button, functions, types
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

API_ID = 23270992
API_HASH = 'd05c08631fcc92a196ee68b0e4ec0606'
BOT_TOKEN = '8448164917:AAHZyK3mjHkNKgAUHtLaxpRZ-6NFkCOCCSY'

ADMINS_FILE = 'admins.json'
SESSIONS_DIR = 'sessions1'
GROUP_LOG = 'group_log.json'
MESSAGES_FILE = 'messages.txt'
CHANNEL_BOT_USERNAME = '@Kanalga_azo_bol_bot'

# Fayllar va papkalarni tayyorlash
os.makedirs(SESSIONS_DIR, exist_ok=True)
for fname in [ADMINS_FILE, GROUP_LOG, MESSAGES_FILE]:
    if not os.path.exists(fname):
        with open(fname, 'w') as f:
            if fname == MESSAGES_FILE:
                for i in range(1, 31):
                    f.write(f"Habar {i}:\nSizga ham shu dastur kerak bo‘lsa @mashhurbek_aka bilan bog‘laning.\n"
                            f"Bu guruh 2025 yilning iyul oylarida ochilgan.\n\n")
            else:
                json.dump([], f)

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
sessions_temp = {}

def is_admin(user_id):
    try:
        with open(ADMINS_FILE) as f:
            admins = json.load(f)
        return str(user_id) in admins
    except:
        return False

async def save_log(admin_id, account_number, group_title, group_id):
    entry = {
        'admin_id': admin_id,
        'account_number': account_number,
        'group_title': group_title,
        'group_id': group_id,
        'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        with open(GROUP_LOG) as f:
            logs = json.load(f)
    except:
        logs = []
    logs.append(entry)
    with open(GROUP_LOG, 'w') as f:
        json.dump(logs, f, indent=2)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if not is_admin(event.sender_id):
        return await event.respond("⛔ Siz admin emassiz.")
    buttons = [
        [Button.inline("📲 Akkount ulash", b"add_account")],
        [Button.inline("👥 Gurux ochish", b"create_groups")],
        [Button.inline("📜 Guruh tarixi", b"group_history")],
        [Button.inline("🧾 Akkountlar ro‘yxati", b"account_list")]
    ]
    await event.respond("👋 Xush kelibsiz, admin!", buttons=buttons)

@bot.on(events.CallbackQuery(data=b'add_account'))
async def cb_add_account(event):
    await event.respond("📞 Telefon raqamingizni +998... ko‘rinishda yuboring.")
    sessions_temp[event.sender_id] = {'step': 'await_phone'}

@bot.on(events.NewMessage)
async def handle_session_steps(event):
    if event.sender_id not in sessions_temp:
        return
    st = sessions_temp[event.sender_id]
    txt = event.raw_text.strip()

    if st['step'] == 'await_phone':
        st['phone'] = txt
        st['step'] = 'await_code'
        cl = TelegramClient(StringSession(), API_ID, API_HASH)
        await cl.connect()
        await cl.send_code_request(txt)
        st['client'] = cl
        return await event.respond("📩 Endi SMS kodi yuboring:")

    if st['step'] == 'await_code':
        cl = st['client']
        phone = st['phone']
        try:
            await cl.sign_in(phone=phone, code=txt)
        except SessionPasswordNeededError:
            st['step'] = 'await_pw'
            return await event.respond("🔐 2-bosqichli parolni yuboring:")
        except PhoneCodeInvalidError:
            return await event.respond("❌ Kod noto‘g‘ri. Qaytadan urinib ko‘ring.")
        sess = cl.session.save()
        with open(f"{SESSIONS_DIR}/{phone}.session", 'w') as f:
            f.write(sess)
        await cl.disconnect()
        del sessions_temp[event.sender_id]
        return await event.respond("✅ Sessiya saqlandi.")

    if st['step'] == 'await_pw':
        cl = st['client']
        phone = st['phone']
        await cl.sign_in(password=txt)
        sess = cl.session.save()
        with open(f"{SESSIONS_DIR}/{phone}.session", 'w') as f:
            f.write(sess)
        await cl.disconnect()
        del sessions_temp[event.sender_id]
        return await event.respond("✅ Sessiya saqlandi.")

@bot.on(events.CallbackQuery(data=b'account_list'))
async def cb_account_list(event):
    files = os.listdir(SESSIONS_DIR)
    if not files:
        return await event.respond("📂 Sessiya topilmadi.")
    msg = "\n".join(f.replace(".session", "") for f in files)
    await event.respond(f"🔐 Ulangan akkountlar:\n{msg}")

@bot.on(events.CallbackQuery(data=b'create_groups'))
async def create_groups(event):
    await event.respond("⏳ Guruhlar ochilishi boshlandi...")
    with open(MESSAGES_FILE) as f:
        messages = [l.strip() for l in f if l.strip()]
    if len(messages) < 30:
        return await event.respond("⚠️ messages.txt da kamida 30 ta xabar bo‘lishi kerak.")
    sessions = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    if not sessions:
        return await event.respond("⚠️ Sessiya topilmadi.")
    for s in sessions:
        phone = s.replace('.session', '')
        with open(os.path.join(SESSIONS_DIR, s)) as f:
            sess_str = f.read()
        cl = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
        await cl.connect()
        try:
            for i in range(1, 51):  # Test uchun 2 ta guruh
                title = f"Guruh_{phone}_{i}"
                try:
                    res = await cl(functions.channels.CreateChannelRequest(
                        title=title,
                        about="Auto-created group",
                        megagroup=True
                    ))
                    ch = res.chats[0]
                    await cl(functions.channels.InviteToChannelRequest(
                        channel=ch.id,
                        users=[CHANNEL_BOT_USERNAME]
                    ))
                    await cl(functions.channels.EditAdminRequest(
                        channel=ch.id,
                        user_id=CHANNEL_BOT_USERNAME,
                        admin_rights=types.ChatAdminRights(
                            post_messages=True,
                            add_admins=False,
                            invite_users=True,
                            change_info=False,
                            delete_messages=True,
                            ban_users=True,
                            pin_messages=True,
                            manage_call=True
                        ),
                        rank="Admin"
                    ))
                    for idx in range(30):
                        await cl.send_message(ch.id, messages[idx])
                        await asyncio.sleep(0.5)
                    await save_log(event.sender_id, phone, title, ch.id)
                    await asyncio.sleep(30)
                except Exception as e:
                    print("🚨 Xato:", e)
        finally:
            await cl.disconnect()
    await event.respond("✅ Barcha guruhlar yaratildi.")

@bot.on(events.CallbackQuery(data=b'group_history'))
async def cb_group_history(event):
    with open(GROUP_LOG) as f:
        logs = json.load(f)
    user_logs = [l for l in logs if str(l['admin_id']) == str(event.sender_id)]
    if not user_logs:
        return await event.respond("🕸 Siz hali guruh yaratmagansiz.")
    txt = "\n".join(f"{i+1}) {l['group_title']} | {l['group_id']} | {l['created_time']}" for i, l in enumerate(user_logs))
    await event.respond(txt[:4000])

print("✅ Kod ishga tayyor.")
bot.run_until_disconnected()