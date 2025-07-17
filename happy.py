import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, CallbackQuery, ContentType,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

API_TOKEN = '7288315068:AAHRG9800i8w6lXIdwlSFcF9YfYJQwo-Qlg'
ADMIN_ID = 7009085528
CHANNEL_ID = -1002510944161
CHANNEL_USERNAME = '@tugilgankun_tabrikg'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎉 Tug'ilgan kun tabriknomasi")],
        [KeyboardButton(text="💍 To‘yga taklifnoma")]
    ], resize_keyboard=True
)

payment_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎬 Video tabrik (45 000)", callback_data="video")],
    [InlineKeyboardButton(text="🎤 Ovozli tabrik (35 000)", callback_data="audio")]
])

class BirthdayOrder(StatesGroup):
    name = State()
    date = State()
    from_who = State()
    wishes = State()
    phone = State()
    type = State()
    photos = State()
    wait_payment_button = State()
    payment = State()

class WeddingOrder(StatesGroup):
    names = State()
    date = State()
    time = State()
    location = State()
    from_who = State()
    type = State()
    wait_payment_button = State()
    payment = State()

admin_requests = {}

@router.message(CommandStart())
async def start_handler(message: Message):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
        if member.status not in ["member", "administrator", "creator"]:
            raise Exception("Not a member")
    except:
        join_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")]])
        await message.answer("📢 Botdan foydalanish uchun kanalga obuna bo‘ling!", reply_markup=join_btn)
        return
    await message.answer("Xush kelibsiz! Iltimos, buyurtma turini tanlang:", reply_markup=main_menu)

@router.message(F.text == "💍 To‘yga taklifnoma")
async def wedding_start(message: Message, state: FSMContext):
    await state.set_state(WeddingOrder.names)
    await message.answer("👰‍♀️🤵 To‘y qahramonlari kimlar?")

@router.message(WeddingOrder.names)
async def wedding_names(message: Message, state: FSMContext):
    await state.update_data(names=message.text)
    await state.set_state(WeddingOrder.date)
    await message.answer("📅 To‘y sanasi?")

@router.message(WeddingOrder.date)
async def wedding_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(WeddingOrder.time)
    await message.answer("🕒 Soat nechada?")

@router.message(WeddingOrder.time)
async def wedding_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(WeddingOrder.location)
    await message.answer("📍 To‘y manzili?")

@router.message(WeddingOrder.location)
async def wedding_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(WeddingOrder.from_who)
    await message.answer("👤 Kim tomonidan yuborilmoqda?")

@router.message(WeddingOrder.from_who)
async def wedding_from(message: Message, state: FSMContext):
    await state.update_data(from_who=message.text)
    await state.set_state(WeddingOrder.type)
    await message.answer(
        "🎁 Taklifnoma turini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Video (60 000)", callback_data="wedding_video")],
            [InlineKeyboardButton(text="🖼 Rasm (45 000)", callback_data="wedding_image")]
        ])
    )

@router.callback_query(F.data.in_(["wedding_video", "wedding_image"]))
async def wedding_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    await state.set_state(WeddingOrder.wait_payment_button)
    await callback.message.answer(
        "💳 To‘lov kartasi: <b>9860 1701 0929 2665</b>\nAkobir Marupov",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="wedding_paid")]])
    )

@router.callback_query(F.data == "wedding_paid")
async def wedding_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WeddingOrder.payment)
    await callback.message.answer("📤 To‘lov chekini yuboring:")

@router.message(WeddingOrder.payment, F.content_type == ContentType.PHOTO)
async def wedding_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username or message.from_user.full_name
    caption = (
        f"🆕 To‘y taklifnomasi:\n"
        f"👫 {data['names']}\n📅 {data['date']} - 🕒 {data['time']}\n📍 {data['location']}\n"
        f"👤 {data['from_who']}\n🎁 {data['type']}\n👤 @{username}"
    )
    buyer_id = message.from_user.id
    admin_requests[buyer_id] = {
        "caption": caption,
        "receipt": message.photo[-1].file_id,
        "photos": []
    }
    confirm_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{buyer_id}")]])
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=confirm_btn)
    await message.answer("✅ Chek yuborildi. Tasdiqlanishi kutilmoqda.")

@router.callback_query(F.data.startswith("approve:"))
async def approve_order(callback: CallbackQuery):
    buyer_id = int(callback.data.split(":")[1])
    data = admin_requests.get(buyer_id)
    if not data:
        await callback.answer("❌ Maʼlumot topilmadi.")
        return
    try:
        await bot.send_message(chat_id=buyer_id, text="✅ Buyurtma tasdiqlandi\n\n" + data['caption'])
        await bot.send_message(chat_id=CHANNEL_ID, text=data['caption'])
        await callback.answer("Tasdiqlandi.")
        del admin_requests[buyer_id]
    except Exception as e:
        await callback.answer(f"Xatolik: {e}")

@router.message(F.text == "🎉 Tug'ilgan kun tabriknomasi")
async def birthday_start(message: Message, state: FSMContext):
    await state.set_state(BirthdayOrder.name)
    await message.answer("🎉 Tabrik kimga?")

@router.message(BirthdayOrder.name)
async def birthday_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BirthdayOrder.date)
    await message.answer("📅 Tug‘ilgan sanasi?")

@router.message(BirthdayOrder.date)
async def birthday_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(BirthdayOrder.from_who)
    await message.answer("👤 Kimdan?")

@router.message(BirthdayOrder.from_who)
async def birthday_from_who(message: Message, state: FSMContext):
    await state.update_data(from_who=message.text)
    await state.set_state(BirthdayOrder.wishes)
    await message.answer("💌 Tabrik matni:")

@router.message(BirthdayOrder.wishes)
async def birthday_wishes(message: Message, state: FSMContext):
    await state.update_data(wishes=message.text)
    await state.set_state(BirthdayOrder.phone)
    await message.answer("📞 Telefon raqam:")

@router.message(BirthdayOrder.phone)
async def birthday_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(BirthdayOrder.type)
    await message.answer("🎁 Tabrik turi:", reply_markup=payment_menu)

@router.callback_query(F.data == "video")
async def birthday_video_selected(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type="video", photos=[])
    await state.set_state(BirthdayOrder.photos)
    await callback.message.answer("🖼 Kamida 20 ta rasm yuboring.")

@router.message(BirthdayOrder.photos, F.content_type == ContentType.PHOTO)
async def birthday_collect_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) < 20:
        await message.answer(f"📸 {len(photos)}/20 rasm. Davom eting.")
    else:
        await state.set_state(BirthdayOrder.wait_payment_button)
        await message.answer(
            "✅ Yetarli rasm olindi.\n💳 Karta: <b>9860 1701 0929 2665</b>\nAkobir Marupov",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="birthday_paid")]]
            )
        )

@router.callback_query(F.data == "audio")
async def birthday_audio_selected(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type="audio", photos=[])
    await state.set_state(BirthdayOrder.wait_payment_button)
    await callback.message.answer(
        "💳 Karta: <b>9860 1701 0929 2665</b>\nAkobir Marupov",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="birthday_paid")]]
        )
    )

@router.callback_query(F.data == "birthday_paid")
async def birthday_paid(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BirthdayOrder.payment)
    await callback.message.answer("📤 Chekni rasm ko‘rinishida yuboring.")

@router.message(BirthdayOrder.payment, F.content_type == ContentType.PHOTO)
async def birthday_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username or message.from_user.full_name
    caption = (
        f"🎉 Tug‘ilgan kun tabrigi:\n"
        f"👤 Kimga: {data['name']}\n📅 {data['date']}\n👥 Kimdan: {data['from_who']}\n"
        f"📞 Tel: {data['phone']}\n💬 Matn: {data['wishes']}\n🎁 Turi: {data['type']}\n👤 @{username}"
    )
    buyer_id = message.from_user.id
    admin_requests[buyer_id] = {
        "caption": caption,
        "receipt": message.photo[-1].file_id,
        "photos": data.get("photos", [])
    }
    confirm_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{buyer_id}")]])
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=confirm_btn)
    await message.answer("✅ Chek yuborildi. Tasdiqlanishi kutilmoqda.")

# >>> AIOHTTP server UptimeRobot uchun <<<
async def handle(request):
    return web.Response(text="Bot is alive!")

async def web_app():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# >>> ASOSIY FUNKSIYA <<<
async def main():
    await web_app()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
