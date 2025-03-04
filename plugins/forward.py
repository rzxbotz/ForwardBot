import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from config import REGEX_PATTERN, LOG_CHANNEL_ID, temp, User
from pyrogram.errors import RPCError, FloodWait, PeerIdInvalid

@Client.on_message(filters.command(["delete"]) & filters.private)
async def delete_files(User, message):
    try:
        des_ch = await User.ask(
            message.from_user.id, 
            "Send me your **Channel ID** or **Username** to scan and delete files."
        )
        chat_id = des_ch.text.strip()

        # Convert username to numeric ID if needed
        try:
            chat_info = await User.get_chat(chat_id)
            chat_id = chat_info.id  
        except PeerIdInvalid:
            return await message.reply(
                "❌ **Error: The userbot hasn't interacted with this channel before.**\n"
                "Try **forwarding a message** from the channel to this userbot first."
            )
        except Exception as e:
            return await message.reply(f"❌ **Invalid Channel ID or Username**\n`{str(e)}`")

    except Exception as e:
        return await message.reply(f"❌ **Error: Cannot access channel**\n`{str(e)}`")

    try:
        last_msg = await User.ask(
            message.from_user.id, 
            "Send me the **last message ID** or **a link to it** from the channel."
        )

        if last_msg.text and not last_msg.forward_date:
            regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?([\w\d_]+)/(\d+)$")
            match = regex.match(last_msg.text.replace("?single", ""))
            if not match:
                return await message.reply('❌ **Invalid message link format.**')

            chat_part = match.group(4)
            last_msg_id = int(match.group(5)) + 1

            if chat_part.isnumeric():
                chat_id = int("-100" + chat_part)
            else:
                try:
                    chat_info = await User.get_chat(chat_part)
                    chat_id = chat_info.id  
                except Exception as e:
                    return await message.reply(f"❌ **Could not fetch channel ID**\n`{str(e)}`")

        elif last_msg.forward_from_chat and last_msg.forward_from_chat.type == enums.ChatType.CHANNEL:
            last_msg_id = int(last_msg.forward_from_message_id) + 1
            chat_id = last_msg.forward_from_chat.id  

    except Exception as e:
        return await message.reply(f"❌ **Error: Could not fetch last message**\n`{str(e)}`")

    first_msg = await User.ask(message.from_user.id, "Enter the **ID of the first message** to start scanning.")
    first_msg_id = max(2, int(first_msg.text.strip()))

    start_time = time.time()
    fetched_count = 0
    deleted_count = 0
    skipped_count = 0

    progress_msg = await message.reply("🗑 **Starting deletion process...**")

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
                retry = 0
                while retry < 3:
                    try:
                        await User.delete_messages(chat_id, msg.id)
                        deleted_count += 1

                        await User.send_message(LOG_CHANNEL_ID, f"🗑 **Deleted:** `{file_name}`")
                        break  

                    except FloodWait as e:
                        retry += 1
                        wait_time = e.value + random.uniform(1, 5)
                        await message.reply(f"🚦 **FloodWait detected!** Waiting `{wait_time:.2f} sec`...")
                        await asyncio.sleep(wait_time)

                await asyncio.sleep(random.uniform(3, 7))

            else:
                skipped_count += 1
                await User.send_message(LOG_CHANNEL_ID, f"⏭ **Skipped:** `{file_name or 'Unknown File'}`")

            elapsed_time = int(time.time() - start_time)
            remaining_files = last_msg_id - i

            try:
                await progress_msg.edit(
                    f"**Deletion in Progress...**\n\n"
                    f"📥 **Fetched:** `{fetched_count}`\n"
                    f"🗑 **Deleted:** `{deleted_count}`\n"
                    f"⏭ **Skipped:** `{skipped_count}`\n"
                    f"⏳ **Time:** `{elapsed_time} sec`\n"
                    f"📌 **Remaining:** `{remaining_files}`"
                )
            except RPCError:
                pass  

        except Exception as e:
            return await message.reply(f"❌ **Error at message `{i}`:** `{str(e)}`")

    total_time = int(time.time() - start_time)
    await progress_msg.edit(
        f"✅ **Deletion Completed!**\n\n"
        f"📥 **Total Fetched:** `{fetched_count}`\n"
        f"🗑 **Total Deleted:** `{deleted_count}`\n"
        f"⏭ **Total Skipped:** `{skipped_count}`\n"
        f"⏳ **Total Time:** `{total_time} sec`"
    )

@Client.on_message(filters.command(["cancel"]) & filters.private)
async def cancel_deletion(User, message):
    temp.CANCEL = True
    await message.reply("🛑 **Deletion process stopped.**")
