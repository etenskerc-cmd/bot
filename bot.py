import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

# ====================== НАСТРОЙКИ ======================
TOKEN = os.getenv("BOT_TOKEN")

MARK = "✨//🌀 ຣครഠຣບ໑ບ சഠཞ౿୶౿ཞ"

HASHTAGS = {
    1: "#art #Satosugu #SuguruGeto #SatoryGojo",
    2: "#NSFW #art #Satosugu #SuguruGeto #SatoryGojo",
    3: "#animation #Satosugu #SuguruGeto #SatoryGojo",
    4: "#NSFW #animation #Satosugu #SuguruGeto #SatoryGojo",
    5: "#cosplay #Satosugu #SuguruGeto #SatoryGojo",
}
# =======================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()


class PostStates(StatesGroup):
    waiting_media = State()
    waiting_link = State()
    waiting_name = State()
    waiting_source = State()


def get_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1. Арт", callback_data="type_1")],
        [InlineKeyboardButton(text="2. NSFW Арт", callback_data="type_2")],
        [InlineKeyboardButton(text="3. Анимация", callback_data="type_3")],
        [InlineKeyboardButton(text="4. NSFW Анимация", callback_data="type_4")],
        [InlineKeyboardButton(text="5. Косплей", callback_data="type_5")],
    ])


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выбери тип поста:",
        reply_markup=get_type_keyboard()
    )


@dp.callback_query(F.data == "new_post")
async def new_post(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Выбери тип поста:",
        reply_markup=get_type_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    post_type = int(callback.data.split("_")[1])
    await state.update_data(post_type=post_type)
    await state.set_state(PostStates.waiting_media)
    
    await callback.message.edit_text("Пришлите медиа")
    await callback.answer()


@dp.message(PostStates.waiting_media, F.photo | F.animation | F.video)
async def get_media(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.animation:
        file_id = message.animation.file_id
        media_type = "animation"
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
    else:
        await message.answer("Пришли фото, гифку или видео.")
        return
    
    await state.update_data(file_id=file_id, media_type=media_type)
    await state.set_state(PostStates.waiting_link)
    
    await message.answer(
        "Медиа получено ✅\nТеперь пришли <b>ссылку на автора</b>:",
        parse_mode=ParseMode.HTML
    )


@dp.message(PostStates.waiting_media)
async def wrong_media(message: Message):
    await message.answer("Нужно прислать именно медиа (фото / гиф / видео).")


@dp.message(PostStates.waiting_link)
async def get_link(message: Message, state: FSMContext):
    link = message.text.strip()
    
    if not (link.startswith("http://") or link.startswith("https://")):
        await message.answer("Пришли нормальную ссылку (начинается с http:// или https://)")
        return
    
    await state.update_data(link=link)
    await state.set_state(PostStates.waiting_name)
    
    await message.answer(
        "Ссылка принята ✅\nТеперь пришли <b>имя автора</b>:",
        parse_mode=ParseMode.HTML
    )


@dp.message(PostStates.waiting_name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(PostStates.waiting_source)
    
    await message.answer(
        "Имя принято ✅\n\n"
        "Укажите источник поста.\n"
        "Пример: X / tumblr / vk / tiktok и т.д."
    )


@dp.message(PostStates.waiting_source)
async def get_source(message: Message, state: FSMContext):
    source = message.text.strip()
    data = await state.get_data()
    
    post_type = data["post_type"]
    file_id = data["file_id"]
    media_type = data["media_type"]
    link = data["link"]
    name = data["name"]
    
    is_nsfw = post_type in (2, 4)
    tags = HASHTAGS.get(post_type, "")
    
    caption = (
        f"{MARK}\n"
        f"\n"
        f"@ <a href=\"{link}\">{name}</a> on {source}\n"
        f"\n"
        f"<blockquote>{tags}</blockquote>"
    )
    
    try:
        if media_type == "photo":
            await message.answer_photo(
                photo=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                has_spoiler=is_nsfw
            )
        elif media_type == "animation":
            await message.answer_animation(
                animation=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                has_spoiler=is_nsfw
            )
        elif media_type == "video":
            await message.answer_video(
                video=file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                has_spoiler=is_nsfw
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сделать ещё один пост", callback_data="new_post")]
        ])
        
        await message.answer(
            "Готовый пост выше ↑",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await message.answer(f"Ошибка при отправке: {e}")
    
    await state.clear()


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
