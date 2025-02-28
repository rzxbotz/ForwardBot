import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from config import REGEX_PATTERN, LOG_CHANNEL_ID, temp
from pyrogram.errors import RPCError

@Client.on_message(filters.private & filters.command(["delete"]))
async def delete_files(client, message):
    try:
        des_ch = await client.ask(message.from_user.id, "Send me your Channel ID to scan and delete files")
        chat_id = int(des_ch.text)
        channel = await client.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f"Error while accessing channel\n{str(e)}")

    try:
        last_msg = await client.ask(message.from_user.id, "Send me the last message from the channel\n(You can also send the link to the last message)")
        if last_msg.text and not last_msg.forward_date:
            regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
            match = regex.match(last_msg.text.replace("?single", ""))
            if not match:
                return await message.reply('Invalid link')
            chat_id = match.group(4)
            last_msg_id = int(match.group(5)) + 1
            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        elif last_msg.forward_from_chat and last_msg.forward_from_chat.type == enums.ChatType.CHANNEL:
            last_msg_id = int(last_msg.forward_from_message_id) + 1
            chat_id = last_msg.forward_from_chat.username or last_msg.forward_from_chat.id
    except Exception as e:
        return await message.reply(f"Error while fetching last message\n{str(e)}")

    first_msg = await client.ask(message.from_user.id, "Enter the ID of the starting message")
    first_msg_id = 2 if int(first_msg.text) < 2 else int(first_msg.text)
    
    start_time = time.time()
    fetched_count = 0
    deleted_count = 0
    skipped_count = 0

    progress_msg = await message.reply("Starting deletion process...")

    for i in range(first_msg_id, last_msg_id):
        if temp.CANCEL:
            break
        try:
            msg = await client.get_messages(chat_id, i)
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
                await client.delete_messages(chat_id, msg.id)
                deleted_count += 1

                # Log deleted file
                await client.send_message(LOG_CHANNEL_ID, f"🗑 **Deleted:** {file_name}")

                # Random delay to prevent flood wait
                await asyncio.sleep(random.uniform(2, 5))
            else:
                skipped_count += 1

                # Log skipped file
                await client.send_message(LOG_CHANNEL_ID, f"⏭ **Skipped:** {file_name}")

            elapsed_time = int(time.time() - start_time)
            remaining_files = (last_msg_id - i)

            try:
                await progress_msg.edit(
                    f"**Deletion in Progress...**\n\n"
                    f"📥 Fetched: {fetched_count}\n"
                    f"🗑 Deleted: {deleted_count}\n"
                    f"⏭ Skipped: {skipped_count}\n"
                    f"⏳ Time: {elapsed_time} sec\n"
                    f"📌 Remaining: {remaining_files}"
                )
            except RPCError:
                pass  # Avoid flood wait on edits

        except Exception as e:
            return await message.reply(f"Error at message {i}: {str(e)}")

    total_time = int(time.time() - start_time)
    await progress_msg.edit(
        f"**Deletion Completed!**\n\n"
        f"📥 Total Fetched: {fetched_count}\n"
        f"🗑 Total Deleted: {deleted_count}\n"
        f"⏭ Total Skipped: {skipped_count}\n"
        f"⏳ Total Time: {total_time} sec"
    )

@Client.on_message(filters.private & filters.command(["cancel"]))
async def cancel_deletion(client, message):
    temp.CANCEL = True
    await message.reply("Deletion process stopped.")
