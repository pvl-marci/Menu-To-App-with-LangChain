from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import CallbackContext
from dotenv import load_dotenv
import aiohttp
import os


# Load environment variables from .env file
load_dotenv()

# Access the TELEGRAM_TOKEN
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Access the API_ENDPOINT
API_ENDPOINT = "http://127.0.0.1:8000/upload"

# Define the function to handle incoming messages


async def start(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to your Menu Creator! Please upload a Photo of your menu.",
    )


async def handle_message(update: Update, context: CallbackContext) -> None:
    # Get the photo file from the message
    photo = update.message.photo[-1]  # Get the highest resolution photo
    photo_file = await photo.get_file()  # Get the file object

    # Download the photo as a byte array
    image_bytes = await photo_file.download_as_bytearray()

    # Send the photo to the FastAPI endpoint
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field(
            "file", image_bytes, filename="image.jpg", content_type="image/jpeg"
        )

        try:
            async with session.post(API_ENDPOINT, data=data) as response:
                content = (
                    await response.json()
                )  # Assuming the FastAPI endpoint returns JSON

                if response.status == 200:
                    # Send the response from the API back to the user
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Your Menu should be ready in your app!",
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Error processing your image.",
                    )
        except aiohttp.ClientError as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"An error occurred: {e}"
            )


def main() -> None:
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add a MessageHandler to handle incoming images
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(CommandHandler("start", start))

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
