# schedule_reader.py
import pandas as pd
from datetime import datetime

PAIR_TIMES = {
    1: "8:00-9:30",
    2: "9:40-11:10",
    3: "11:20-12:50",
    4: "13:15-14:45",
    5: "15:00-16:30",
    6: "16:40-18:10",
    7: "18:20-19:50",
    8: "19:55-21:25",
}


def load_schedule(path: str):
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    # Убедимся, что колонка 'Неделя' - строковая
    df['Неделя'] = df['Неделя'].astype(str)
    return df


def get_groups(df):
    return sorted(df["Группа"].unique())


def get_week_parity():
    """
    Определяет четность текущей учебной недели
    Возвращает: '1' - нечетная, '2' - четная (СТРОКА!)
    """
    # Фиксированная точка отсчета - 2 сентября 2024 была нечетная неделя
    reference_date = datetime(2024, 9, 2).date()  # Нечетная неделя
    today = datetime.now().date()

    # Разница в днях
    days_diff = (today - reference_date).days

    # Разница в неделях
    weeks_diff = days_diff // 7

    # Если разница в неделях четная - значит та же четность, что и reference
    # Если нечетная - противоположная четность
    if weeks_diff % 2 == 0:
        return '1'  # Нечетная неделя (СТРОКА!)
    else:
        return '2'  # Четная неделя (СТРОКА!)


def is_odd_week():
    """Для обратной совместимости - возвращает boolean"""
    return get_week_parity() == '1'


def get_schedule_day(df, group, day, week_parity=None, subgroup=None):
    day_df = df[(df['Группа'] == group) & (df['День'] == day)]

    # фильтр по неделе
    if week_parity:
        day_df = day_df[(day_df['Неделя'] == str(week_parity)) | (day_df['Неделя'] == '-')]

    # фильтр по подгруппе
    if subgroup:
        day_df = day_df[(day_df['Подгруппа'] == str(subgroup)) | (day_df['Подгруппа'] == '-')]

    if day_df.empty:
        return "❌ Пар нет."

    day_df = day_df.sort_values(by='Пара')

    out = ""

    for _, row in day_df.iterrows():
        para = int(row['Пара'])
        time = PAIR_TIMES.get(para, "Время неизвестно")
        sub = f"[{row['Подгруппа']}]" if row['Подгруппа'] != '-' else ""
        week = f"({row['Неделя']} неделя)" if row['Неделя'] in ['1', '2'] else ""

        out += (
            f"{para}. {sub} {row['Предмет']} {week}\n"
            f"{row['Преподаватель']} • {row['Аудитория']}\n"
            f"{time}\n\n"
        )

    return out.strip()



def get_schedule_week(df, group, week_parity, subgroup=None):
    days = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']
    out = "📚 Расписание на эту неделю:\n\n"

    for d in days:
        out += f"📅 {d}\n"
        out += get_schedule_day(df, group, d, week_parity, subgroup)
        out += "\n\n"

    return out.strip()
