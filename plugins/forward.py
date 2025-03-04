import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, PeerIdInvalid
from config import User, LOG_CHANNEL, DELETE_REGEX, temp  # Add DELETE_REGEX in config

@Client.on_message(filters.command("delete") & filters.private)
async def start_delete(_, message):
    try:
        ch_msg = await message.chat.ask("Send me the **Channel ID or Username** where I should delete files.")
        chat_id = ch_msg.text.strip()

        if chat_id.isnumeric():
            chat_id = int("-100" + chat_id)  # Convert to Telegram ID format

        # Ensure the bot interacts with the channel to fix PEER_ID_INVALID
        try:
            channel = await User.get_chat(chat_id)
        except PeerIdInvalid:
            return await message.reply("❌ **Error:** Unable to fetch the channel. Ensure the bot is in the channel.")

        regex_pattern = re.compile(DELETE_REGEX, re.IGNORECASE)
        total_deleted = 0
        total_skipped = 0

        # Confirm before starting
        confirm_msg = await message.chat.ask(
            f"🚨 **Confirm Deletion?**\n\n"
            f"Channel: `{chat_id}`\n"
            f"Regex: `{DELETE_REGEX}`\n\n"
            f"Type `YES` to proceed."
        )
        if confirm_msg.text.lower() != "yes":
            return await message.reply("🚫 **Deletion Cancelled!**")

        k = await message.reply("🔄 **Starting deletion...**")

        # Fetch all messages in the channel
        async for msg in User.get_chat_history(chat_id):
            if temp.CANCEL:
                break

            if not msg.media:
                continue  # Ignore non-media messages

            file_name = None
            if msg.document:
                file_name = msg.document.file_name
            elif msg.video:
                file_name = msg.video.file_name
            elif msg.audio:
                file_name = msg.audio.file_name

            if not file_name or not regex_pattern.search(file_name):
                total_skipped += 1
                log_text = f"⏭️ **Skipped:** `{file_name}`"
                await User.send_message(LOG_CHANNEL, log_text)
                continue

            try:
                await msg.delete()
                total_deleted += 1
                log_text = f"🗑️ **Deleted:** `{file_name}`"
                await User.send_message(LOG_CHANNEL, log_text)

                # Random sleep for flood wait handling
                await asyncio.sleep(random.uniform(2, 5))

            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception as err:
                await User.send_message(LOG_CHANNEL, f"⚠️ **Error:** {err}")

            # Update progress
            elapsed_time = int(time.time() - temp.START_TIME) // 60
            try:
                await k.edit(
                    f"🗑️ **Deleting Files...**\n\n"
                    f"✅ Deleted: {total_deleted}\n"
                    f"⏭️ Skipped: {total_skipped}\n"
                    f"⏳ Elapsed Time: {elapsed_time} min"
                )
            except:
                pass  # Ignore edit errors (FloodWait)

        await k.edit(
            f"✅ **Deletion Completed!**\n\n"
            f"🗑️ Total Deleted: {total_deleted}\n"
            f"⏭️ Total Skipped: {total_skipped}"
        )

    except Exception as e:
        await message.reply(f"❌ **Error:** {e}")
        await User.send_message(LOG_CHANNEL, f"⚠️ **Error in deletion:** {e}")

@Client.on_message(filters.chat(LOG_CHANNEL) & filters.regex(DELETE_REGEX))
async def delete_upcoming(client, message):
    """Delete upcoming regex-matching files in the channel."""
    try:
        await message.delete()
        await User.send_message(LOG_CHANNEL, f"🗑️ **Deleted New File:** `{message.caption or 'No Caption'}`")
    except Exception as e:
        await User.send_message(LOG_CHANNEL, f"⚠️ **Error Deleting File:** {e}")

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_delete(_, message):
    temp.CANCEL = True
    await message.reply("🚫 **Deletion Stopped!**")
