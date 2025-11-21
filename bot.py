# bot.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from schedule_reader import load_schedule, get_groups, get_schedule_day, get_schedule_week, is_odd_week, get_week_parity

TOKEN = "7888089291:AAGs70w9wQG6nls8Ph9mbBmCGl2i8ofdDVY"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Загружаем Excel
SCHEDULE_DF = load_schedule("data/biophac_schedule.xlsx")
GROUPS_LIST = get_groups(SCHEDULE_DF)

# Кнопки групп
group_buttons = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=g)] for g in GROUPS_LIST],
    resize_keyboard=True
)

# Кнопки дней
days_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сегодня"), KeyboardButton(text="Завтра")],
        [KeyboardButton(text="На эту неделю"), KeyboardButton(text="На следующую неделю")],
        [KeyboardButton(text="Сменить группу")]
    ],
    resize_keyboard=True
)

user_group = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! 👋 Выбери свою группу:", reply_markup=group_buttons)


@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Выбор группы
    if text in GROUPS_LIST:
        user_group[chat_id] = text
        await message.answer(f"✅ Группа {text} выбрана!", reply_markup=days_buttons)
        return

    # Смена группы
    if text == "Сменить группу":
        user_group.pop(chat_id, None)
        await message.answer("Выбери свою группу:", reply_markup=group_buttons)
        return

    # Если группа не выбрана
    if chat_id not in user_group:
        await message.answer("Сначала выбери свою группу:", reply_markup=group_buttons)
        return

    group = user_group[chat_id]
    current_week_parity = is_odd_week()
    # В handle_message после week_parity = is_odd_week()
    debug_info = f"Текущая неделя: {'НЕЧЕТНАЯ' if current_week_parity else 'ЧЕТНАЯ'}"
    print(f"DEBUG: {debug_info}")  # Это увидшь в консоли

    # Сегодня
    if text == "Сегодня":
        from datetime import datetime
        today = datetime.now()
        day_name = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"][today.weekday()]
        sched = get_schedule_day(SCHEDULE_DF, group, day_name, current_week_parity)
        week_type = "нечетная" if current_week_parity else "четная"
        await message.answer(f"📅 Расписание для {group} — {day_name} ({week_type} неделя):\n\n{sched}")
        return

    # Завтра
    if text == "Завтра":
        from datetime import datetime, timedelta
        tomorrow = datetime.now() + timedelta(days=1)
        if tomorrow.weekday() >= 6:  # Воскресенье
            await message.answer("❌ Завтра нет занятий.")
            return

        # Проверяем, не перешли ли мы на следующую неделю
        tomorrow_week_parity = current_week_parity
        if datetime.now().weekday() == 6:  # Если сегодня воскресенье
            tomorrow_week_parity = not current_week_parity

        day_name = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"][tomorrow.weekday()]
        sched = get_schedule_day(SCHEDULE_DF, group, day_name, tomorrow_week_parity)
        week_type = "нечетная" if tomorrow_week_parity else "четная"
        await message.answer(f"📅 Расписание для {group} — {day_name} ({week_type} неделя):\n\n{sched}")
        return

    # Неделя
    if text == "На эту неделю":
        current_week = get_week_parity()  # '1' или '2' (СТРОКА!)
        sched = get_schedule_week(SCHEDULE_DF, group, current_week)
        await message.answer(sched)
        return

    if text == "На следующую неделю":
        current_week = get_week_parity()  # '1' или '2' (СТРОКА!)
        next_week = '2' if current_week == '1' else '1'  # Инвертируем: '1'->'2', '2'->'1'
        sched = get_schedule_week(SCHEDULE_DF, group, next_week)
        await message.answer(sched)
        return

    await message.answer("Не понимаю 😅 Используй кнопки ниже.", reply_markup=days_buttons)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    print("Бот запущен!")
    asyncio.run(dp.start_polling(bot))