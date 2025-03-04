import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from config import User, temp, LOG_CHANNEL, DELETE_REGEX
from pyrogram.errors import FloodWait

@Client.on_message(filters.private & filters.command(["delete"]))
async def delete_files(client, message):
    try:
        des_ch = await client.ask(message.from_user.id, "Send Me Your Channel ID (The Channel to Delete Files From)")
        chat_id = int(des_ch.text)
        target_channel = await User.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f"Error While Getting Target Channel\n{str(e)}")

    regex_pattern = re.compile(DELETE_REGEX, re.IGNORECASE)

    last_msg = await client.ask(message.from_user.id, "Forward the last message from the CHANNEL (or send a link to it)")
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

    first_msg = await client.ask(message.from_user.id, "**Enter the ID of the starting message to check**")
    first_msg_id = 2 if int(first_msg.text) < 2 else int(first_msg.text)
    start_time = time.time()
    deleted_count = 0
    skipped_count = 0  

    log_message = await message.reply("Starting Deletion...")

    for i in range(first_msg_id, last_msg_id):
        if temp.CANCEL:
            break
        try:
            i_msg = await User.get_messages(target_channel.id, i)

            if not i_msg.media:
                skipped_count += 1
                continue

            file_name = None

            if i_msg.document:
                file_name = i_msg.document.file_name
            elif i_msg.video:
                file_name = i_msg.video.file_name
            elif i_msg.audio:
                file_name = i_msg.audio.file_name

            if not file_name or not regex_pattern.search(file_name):
                skipped_count += 1
                continue

            await User.delete_messages(target_channel.id, i)
            deleted_count += 1

            await User.send_message(
                LOG_CHANNEL,
                f"🗑 Deleted: {file_name}"
            )

            # Add random sleep here (between 2 to 5 seconds)
            random_sleep_time = random.uniform(2, 5)
            await asyncio.sleep(random_sleep_time)

        except FloodWait as e:
            await message.reply(f"Flood Wait Error! Waiting for {e.value + 1} seconds...")
            await asyncio.sleep(e.value + 1)
        except Exception as e:
            print(f"Deletion stopped due to: {e}")
            return await message.reply(f"Process Stopped at {i}\nCheck Logs for More Info")

        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        try:
            await log_message.edit(
                f"**Deletion in Progress...**\n\n"
                f"🗑 Deleted: {deleted_count}\n"
                f"⏭️ Skipped: {skipped_count}\n"
                f"⏳ Elapsed Time: {elapsed_minutes} min"
            )
            await asyncio.sleep(2)
        except Exception:
            pass

    total_time = time.time() - start_time
    total_minutes = int(total_time // 60)
    await log_message.edit(
        f"**Deletion Completed!**\n\n"
        f"🗑 Total Deleted: {deleted_count}\n"
        f"⏭️ Total Skipped: {skipped_count}\n"
        f"⏳ Total Time: {total_minutes} min"
    )

@Client.on_message(filters.private & filters.command(["cancel"]))
async def cancel_deletion(bot, message):
    temp.CANCEL = True
    await message.reply("Deletion Stopped")
