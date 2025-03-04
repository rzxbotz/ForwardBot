import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, PeerIdInvalid, RPCError
from config import User, LOG_CHANNEL, DELETE_REGEX, temp


async def ensure_peer(client, chat_id):
    """Ensure the bot has interacted with the channel before deleting messages."""
    try:
        await client.get_chat(chat_id)  # Fetch channel info
        return True
    except PeerIdInvalid:
        return False


@Client.on_message(filters.command("delete") & filters.private)
async def start_delete(_, message):
    try:
        ch_msg = await message.chat.ask("📌 **Send me the Channel ID or Username** to delete files from.")
        chat_id = ch_msg.text.strip()

        if chat_id.isnumeric():
            chat_id = int("-100" + chat_id)  # Convert to Telegram ID format

        # Ensure interaction with the channel
        if not await ensure_peer(User, chat_id):
            return await message.reply("❌ **Error:** Bot hasn't interacted with the channel yet. Send a message there first.")

        regex_pattern = re.compile(DELETE_REGEX, re.IGNORECASE)
        total_deleted, total_skipped = 0, 0
        temp.CANCEL = False

        confirm_msg = await message.chat.ask(
            f"🚨 **Confirm Deletion?**\n\n"
            f"🆔 Channel: `{chat_id}`\n"
            f"🔍 Regex: `{DELETE_REGEX}`\n\n"
            f"Type `YES` to proceed."
        )
        if confirm_msg.text.lower() != "yes":
            return await message.reply("🚫 **Deletion Cancelled!**")

        k = await message.reply("🔄 **Starting Deletion...**")
        temp.START_TIME = time.time()

        async for msg in User.get_chat_history(chat_id):
            if temp.CANCEL:
                break

            if not msg.media:
                continue  # Ignore non-media messages

            file_name = get_file_name(msg)

            if not file_name or not regex_pattern.search(file_name):
                total_skipped += 1
                await log_action(f"⏭️ **Skipped:** `{file_name or 'Unknown File'}`")
                continue

            try:
                await msg.delete()
                total_deleted += 1
                await log_action(f"🗑️ **Deleted:** `{file_name}`")

                await asyncio.sleep(random.uniform(2, 5))  # Random sleep to avoid flood wait

            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except RPCError as err:
                await log_action(f"⚠️ **Error:** {err}")

            elapsed_time = int(time.time() - temp.START_TIME) // 60
            try:
                await k.edit(
                    f"🗑️ **Deleting Files...**\n\n"
                    f"✅ Deleted: {total_deleted}\n"
                    f"⏭️ Skipped: {total_skipped}\n"
                    f"⏳ Elapsed Time: {elapsed_time} min"
                )
            except:
                pass

        await k.edit(
            f"✅ **Deletion Completed!**\n\n"
            f"🗑️ Total Deleted: {total_deleted}\n"
            f"⏭️ Total Skipped: {total_skipped}"
        )

    except Exception as e:
        await log_action(f"⚠️ **Error in deletion:** {e}")


async def log_action(log_text):
    """Log actions to the log channel while ensuring peer validity."""
    try:
        if await ensure_peer(User, LOG_CHANNEL):
            await User.send_message(LOG_CHANNEL, log_text)
    except PeerIdInvalid:
        pass  # Skip logging if peer is invalid


@Client.on_message(filters.chat(LOG_CHANNEL) & filters.regex(DELETE_REGEX))
async def delete_upcoming(client, message):
    """Automatically delete new regex-matching files in the channel."""
    try:
        await message.delete()
        await log_action(f"🗑️ **Deleted New File:** `{message.caption or 'No Caption'}`")
    except Exception as e:
        await log_action(f"⚠️ **Error Deleting File:** {e}")


@Client.on
