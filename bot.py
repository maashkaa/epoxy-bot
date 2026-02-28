from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import os

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = 891530001
PASSWORD = "EPOXY2026"

ASK_PASSWORD, LENGTH, WIDTH, HEIGHT, RATIO, EXTRA = range(6)

authorized_users = set()

ratios = [
    "2:1", "3:1", "4:1", "1:1",
    "10:1", "100:60", "100:50", "100:40",
    "10:6", "10:4", "1:5", "1:20"
]

extra_options = ["Без запаса", "+5%", "+10%"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in authorized_users:
        await update.message.reply_text("Введите длину в см:")
        return LENGTH

    await update.message.reply_text(
        "Добро пожаловать в калькулятор эпоксидной смолы RUKOSA.\n\nВведите пароль:"
    )
    return ASK_PASSWORD


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == PASSWORD:
        authorized_users.add(update.effective_user.id)
        await update.message.reply_text("Доступ разрешен.\nВведите длину в см:")
        return LENGTH
    else:
        await update.message.reply_text("Неверный пароль.")
        return ASK_PASSWORD


async def get_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["length"] = float(update.message.text)
    await update.message.reply_text("Введите ширину в см:")
    return WIDTH


async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["width"] = float(update.message.text)
    await update.message.reply_text("Введите толщину в мм:")
    return HEIGHT


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = float(update.message.text)

    keyboard = [ratios[i:i+4] for i in range(0, len(ratios), 4)]
    await update.message.reply_text(
        "Выберите пропорцию:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return RATIO


async def get_ratio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ratio"] = update.message.text

    await update.message.reply_text(
        "Добавить запас?",
        reply_markup=ReplyKeyboardMarkup([extra_options], resize_keyboard=True)
    )
    return EXTRA


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = context.user_data["length"]
    width = context.user_data["width"]
    height_mm = context.user_data["height"]
    ratio_text = context.user_data["ratio"]

    height_cm = height_mm / 10
    volume_liters = (length * width * height_cm) / 1000

    extra = update.message.text
    if extra == "+5%":
        volume_liters *= 1.05
    elif extra == "+10%":
        volume_liters *= 1.10

    part_a, part_b = map(float, ratio_text.split(":"))
    total_parts = part_a + part_b

    resin = volume_liters * part_a / total_parts
    hardener = volume_liters * part_b / total_parts

    result = (
        f"Размер: {length} x {width} x {height_mm} мм\n\n"
        f"Общий объем смеси: {volume_liters:.2f} л\n"
        f"Пропорция: {ratio_text}\n\n"
        f"Смола: {resin:.2f} л\n"
        f"Отвердитель: {hardener:.2f} л\n\n"
        "Расчет завершен.\n"
        "Вы можете отправить фото готовой работы."
    )

    await update.message.reply_text(result)
    return ConversationHandler.END


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    caption = (
        f"Новая работа\n\n"
        f"Имя: {user.first_name}\n"
        f"Username: @{user.username}\n"
        f"ID: {user.id}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption
    )

    await update.message.reply_text("Фото получено. Спасибо.")


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
        LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_length)],
        WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
        HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
        RATIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ratio)],
        EXTRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate)],
    },
    fallbacks=[],
)

app.add_handler(conv_handler)
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()
