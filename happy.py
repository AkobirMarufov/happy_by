import asyncio
import logging
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

import os
from dotenv import load_dotenv
load_dotenv(".env")

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
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

# Tug'ilgan kun funksiyalari ... (qolgani o'zgarishsiz qoldi)

@router.message(F.text == "💍 To‘yga taklifnoma")
async def wedding_start(message: Message, state: FSMContext):
    await state.set_state(WeddingOrder.names)
    await message.answer("👰‍♀️🤵 To‘y qahramonlari kimlar? (masalan: Ali va Nodira)")

@router.message(WeddingOrder.names)
async def wedding_names(message: Message, state: FSMContext):
    await state.update_data(names=message.text)
    await state.set_state(WeddingOrder.date)
    await message.answer("📅 To‘y qachon bo‘ladi? (masalan: 21.08.2025)")

@router.message(WeddingOrder.date)
async def wedding_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(WeddingOrder.time)
    await message.answer("🕒 To‘y soati nechada bo‘ladi?")

@router.message(WeddingOrder.time)
async def wedding_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(WeddingOrder.location)
    await message.answer("📍 To‘y joyi (Restoran nomi va manzili)?")

@router.message(WeddingOrder.location)
async def wedding_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(WeddingOrder.from_who)
    await message.answer("👤 Kim tomonidan taklifnoma yuborilmoqda?")

@router.message(WeddingOrder.from_who)
async def wedding_from(message: Message, state: FSMContext):
    await state.update_data(from_who=message.text)
    await state.set_state(WeddingOrder.type)
    await message.answer(
        "🎁 Taklifnoma turini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎬 Video taklifnoma (60 000)", callback_data="wedding_video")],
                [InlineKeyboardButton(text="🖼 Rasmli taklifnoma (40 000)", callback_data="wedding_image")]
            ]
        )
    )

@router.callback_query(F.data.in_(["wedding_video", "wedding_image"]))
async def wedding_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    await state.set_state(WeddingOrder.wait_payment_button)
    await callback.message.answer(
        "💳 To‘lov qilish uchun quyidagi karta raqamidan foydalaning:\n"
        "<b>9860 1701 0929 2665</b>\nAkobir Marupov",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="wedding_paid")]]
        )
    )

@router.callback_query(F.data == "wedding_paid")
async def wedding_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WeddingOrder.payment)
    await callback.message.answer("📤 Endi to‘lov chekini rasm ko‘rinishida yuboring:")

@router.message(WeddingOrder.payment, F.content_type == ContentType.PHOTO)
async def wedding_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username or message.from_user.full_name
    caption = (
        f"🆕 Yangi to‘y taklifnoma buyurtmasi:\n"
        f"👫 To‘y qahramonlari: {data['names']}\n"
        f"📅 Sana: {data['date']} - 🕒 Soat: {data['time']}\n"
        f"📍 Joyi: {data['location']}\n"
        f"👤 Kim tomondan: {data['from_who']}\n"
        f"💰 Taklifnoma turi: {data['type'].replace('wedding_', '')}\n"
        f"👤 Buyurtmachi: @{username}"
    )
    buyer_id = message.from_user.id
    admin_requests[buyer_id] = {
        "caption": caption,
        "receipt": message.photo[-1].file_id,
        "photos": []
    }
    confirm_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{buyer_id}")]
    ])
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=confirm_btn)
    await message.answer("✅ Chekingiz adminga yuborildi. Tasdiqlanishi kutilmoqda.")

@router.callback_query(F.data.startswith("approve:"))
async def approve_order(callback: CallbackQuery):
    buyer_id = int(callback.data.split(":")[1])
    data = admin_requests.get(buyer_id)
    if not data:
        await callback.answer("❌ Maʼlumot topilmadi.")
        return
    try:
        await bot.send_message(chat_id=buyer_id, text="✅ Buyurtmangiz tasdiqlandi.\n\n" + data['caption'])
        await bot.send_message(chat_id=CHANNEL_ID, text=data['caption'])
        for photo_id in data.get("photos", []):
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id)
        await callback.answer("Buyurtma tasdiqlandi.")
        del admin_requests[buyer_id]
    except Exception as e:
        await callback.answer(f"Xatolik: {e}")

@router.message(F.text == "🎉 Tug'ilgan kun tabriknomasi")
async def birthday_start(message: Message, state: FSMContext):
    await state.set_state(BirthdayOrder.name)
    await message.answer("🎉 Tabrik kim uchun? (Ismini yozing)")

@router.message(BirthdayOrder.name)
async def birthday_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BirthdayOrder.date)
    await message.answer("📅 Tug‘ilgan kuni qachon? (masalan: 12.09.2000)")

@router.message(BirthdayOrder.date)
async def birthday_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(BirthdayOrder.from_who)
    await message.answer("👤 Tabrik kimdan? (Ism yoki familiya)")

@router.message(BirthdayOrder.from_who)
async def birthday_from_who(message: Message, state: FSMContext):
    await state.update_data(from_who=message.text)
    await state.set_state(BirthdayOrder.wishes)
    await message.answer("💌 Tabrik matnini yozing:")

@router.message(BirthdayOrder.wishes)
async def birthday_wishes(message: Message, state: FSMContext):
    await state.update_data(wishes=message.text)
    await state.set_state(BirthdayOrder.phone)
    await message.answer("📞 Telefon raqam kiriting (aloqa uchun):")

@router.message(BirthdayOrder.phone)
async def birthday_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(BirthdayOrder.type)
    await message.answer("🎁 Tabrik turini tanlang:", reply_markup=payment_menu)

@router.callback_query(F.data == "video")
async def birthday_video_selected(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type="video", photos=[])
    await state.set_state(BirthdayOrder.photos)
    await callback.message.answer("🖼 Iltimos, kamida 20 ta rasm yuboring. Birgalikda yoki alohida yuborishingiz mumkin.")

@router.message(BirthdayOrder.photos, F.content_type == ContentType.PHOTO)
async def birthday_collect_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

    if len(photos) < 20:
        await message.answer(f"📸 {len(photos)}/20 rasm qabul qilindi. Davom eting...")
    else:
        await state.set_state(BirthdayOrder.wait_payment_button)
        await message.answer(
            "✅ Yetarli rasm olindi.\n\n💳 Endi to‘lov uchun karta raqamidan foydalaning:\n"
            "<b>9860 1701 0929 2665</b>\nAkobir Marupov",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="birthday_paid")]]
            )
        )

@router.callback_query(F.data == "audio")
async def birthday_audio_selected(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type="audio", photos=[])
    await state.set_state(BirthdayOrder.wait_payment_button)
    await callback.message.answer(
        "💳 To‘lov uchun karta raqami:\n"
        "<b>9860 1701 0929 2665</b>\nAkobir Marupov",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ To‘lov qildim", callback_data="birthday_paid")]]
        )
    )

@router.callback_query(F.data == "birthday_paid")
async def birthday_paid(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BirthdayOrder.payment)
    await callback.message.answer("📤 Iltimos, to‘lov chekini rasm ko‘rinishida yuboring:")

@router.message(BirthdayOrder.payment, F.content_type == ContentType.PHOTO)
async def birthday_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.from_user.username or message.from_user.full_name
    caption = (
        f"🎉 Yangi tug‘ilgan kun tabrigi buyurtmasi:\n"
        f"👤 Tabrik kimga: {data['name']}\n"
        f"📅 Sana: {data['date']}\n"
        f"👥 Kimdan: {data['from_who']}\n"
        f"📞 Aloqa: {data['phone']}\n"
        f"💬 Tabrik matni: {data['wishes']}\n"
        f"🎁 Turi: {data['type']}\n"
        f"👤 Buyurtmachi: @{username}"
    )
    buyer_id = message.from_user.id
    admin_requests[buyer_id] = {
        "caption": caption,
        "receipt": message.photo[-1].file_id,
        "photos": data.get("photos", [])
    }
    confirm_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{buyer_id}")]
    ])
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=confirm_btn)
    await message.answer("✅ Chekingiz adminga yuborildi. Tasdiqlanishi kutilmoqda.")

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

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())