import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from config import REGEX_PATTERN, LOG_CHANNEL_ID, temp, User
from pyrogram.errors import RPCError, PeerIdInvalid

@Client.on_message(filters.private & filters.command(["delete"]))
async def delete_files(User, message):
    try:
        des_ch = await User.ask(message.from_user.id, "Send me your Channel ID or Username to scan and delete files")
        chat_id = des_ch.text.strip()

        # Convert username to numeric ID if needed
        if chat_id.startswith("@") or not chat_id.startswith("-100"):
            try:
                chat_info = await User.get_chat(chat_id)
                chat_id = chat_info.id
            except Exception as e:
                return await message.reply(f"❌ Error: Invalid Channel ID or Username\n`{str(e)}`")

        # Ensure user has access
        channel = await User.get_chat(chat_id)

    except PeerIdInvalid:
        return await message.reply(
            "❌ Error: The user hasn't interacted with this channel before.\n"
            "Try forwarding a message from the channel to this user first."
        )
    except Exception as e:
        return await message.reply(f"❌ Error: Cannot access channel\n`{str(e)}`")

    try:
        last_msg = await User.ask(message.from_user.id, "Send me the last message from the channel (or a link to it)")
        if last_msg.text and not last_msg.forward_date:
            regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
            match = regex.match(last_msg.text.replace("?single", ""))
            if not match:
                return await message.reply('❌ Invalid message link.')
            chat_id = match.group(4)
            last_msg_id = int(match.group(5)) + 1
            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        elif last_msg.forward_from_chat and last_msg.forward_from_chat.type == enums.ChatType.CHANNEL:
            last_msg_id = int(last_msg.forward_from_message_id) + 1
            chat_id = last_msg.forward_from_chat.username or last_msg.forward_from_chat.id
    except Exception as e:
        return await message.reply(f"❌ Error: Could not fetch last message\n`{str(e)}`")

    first_msg = await User.ask(message.from_user.id, "Enter the ID of the starting message")
    first_msg_id = max(2, int(first_msg.text.strip()))

    start_time = time.time()
    fetched_count = 0
    deleted_count = 0
    skipped_count = 0

    progress_msg = await message.reply("🗑 Starting deletion process...")

    for i in range(first_msg_id, last_msg_id):
        if temp.CANCEL:
            break
        try:
            msg = await User.get_messages(chat_id, i)
            fetched_count += 1

            if not msg.media:
                skipped_count += 1
                continue

            file_name = None
            if msg.document:
                file_name = msg.document.file_name
            elif msg.video:
                file_name = msg.video.file_name
            elif msg.audio:
                file_name = msg.audio.file_name

            if file_name and re.search(REGEX_PATTERN, file_name, re.IGNORECASE):
                await User.delete_messages(chat_id, msg.id)
                deleted_count += 1

                # Log deleted file
                await User.send_message(LOG_CHANNEL_ID, f"🗑 **Deleted:** `{file_name}`")

                # Random delay to prevent flood wait
                await asyncio.sleep(random.uniform(2, 5))
            else:
                skipped_count += 1

                # Log skipped file
                await User.send_message(LOG_CHANNEL_ID, f"⏭ **Skipped:** `{file_name or 'Unknown File'}`")

            elapsed_time = int(time.time() - start_time)
            remaining_files = last_msg_id - i

            try:
                await progress_msg.edit(
                    f"**Deletion in Progress...**\n\n"
                    f"📥 Fetched: `{fetched_count}`\n"
                    f"🗑 Deleted: `{deleted_count}`\n"
                    f"⏭ Skipped: `{skipped_count}`\n"
                    f"⏳ Time: `{elapsed_time} sec`\n"
                    f"📌 Remaining: `{remaining_files}`"
                )
            except RPCError:
                pass  # Avoid flood wait on frequent updates

        except Exception as e:
            return await message.reply(f"❌ Error at message `{i}`: `{str(e)}`")

    total_time = int(time.time() - start_time)
    await progress_msg.edit(
        f"✅ **Deletion Completed!**\n\n"
        f"📥 Total Fetched: `{fetched_count}`\n"
        f"🗑 Total Deleted: `{deleted_count}`\n"
        f"⏭ Total Skipped: `{skipped_count}`\n"
        f"⏳ Total Time: `{total_time} sec`"
    )

@Client.on_message(filters.private & filters.command(["cancel"]))
async def cancel_deletion(User, message):
    temp.CANCEL = True
    await message.reply("🛑 Deletion process stopped.")
