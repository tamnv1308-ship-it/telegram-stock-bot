import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = "1_HsUZzPCV1v3Ei8VmbvbMw0Jpdtni5ygIDFx5RNwJ8w"

URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=DATA"


def load_data():
    df = pd.read_csv(URL)

    df["Mã sản phẩm"] = (
        pd.to_numeric(df["Mã sản phẩm"], errors="coerce")
        .fillna(0)
        .astype("int64")
        .astype(str)
    )

    for col in [
        "Số lượng có thể bán",
        "Tổng số lượng",
        "Số lượng thực tế",
        "Số lượng đang đi đường",
        "Số lượng đã đặt"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    try:

        df = load_data()

        # ALL MÃ SP
        if text.lower().startswith("all "):

            code = text[4:].strip().lstrip("0")

            result = df[df["Mã sản phẩm"] == code]

            result = result[result["Số lượng có thể bán"] > 0]

            if result.empty:
                await update.message.reply_text("❌ Không có shop nào còn hàng")
                return

            name = result.iloc[0]["Tên sản phẩm"]

            msg = f"📦 {name}\n\n🏪 Danh sách ST còn hàng\n\n"

            for _, row in result.sort_values(
                by="Số lượng có thể bán",
                ascending=False
            ).iterrows():

                msg += (
                    f"{row['Mã siêu thị']} - "
                    f"{row['Tên siêu thị']} : "
                    f"{int(row['Số lượng có thể bán'])}\n"
                )

            await update.message.reply_text(msg[:4000])

            return

        # TRA MÃ SP
        code = text.lstrip("0")

        result = df[df["Mã sản phẩm"] == code]

        if result.empty:
            await update.message.reply_text(
                "❌ Không tìm thấy mã sản phẩm"
            )
            return

        name = result.iloc[0]["Tên sản phẩm"]

        coban = int(result["Số lượng có thể bán"].sum())

        shops = result[result["Số lượng có thể bán"] > 0]

        so_shop = len(shops)

        top10 = shops.sort_values(
            by="Số lượng có thể bán",
            ascending=False
        ).head(10)

        msg = (
            f"📦 {name}\n\n"
            f"📊 Tồn có thể bán toàn quốc\n"
            f"• Có thể bán: {coban}\n"
            f"• Shop còn hàng: {so_shop}\n\n"
            f"🏪 Top 10 shop tồn nhiều nhất\n\n"
        )

        for _, row in top10.iterrows():

            msg += (
                f"{row['Mã siêu thị']} - "
                f"{row['Tên siêu thị']} : "
                f"{int(row['Số lượng có thể bán'])}\n"
            )

        msg += f"\n📌 Xem toàn bộ shop:\nall {text}"

        await update.message.reply_text(msg)

    except Exception as e:

        await update.message.reply_text(f"❌ Lỗi:\n{e}")


app = Application.builder().token(TOKEN).build()

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
)

app.run_polling()
