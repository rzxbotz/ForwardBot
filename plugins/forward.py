import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from config import CAPTION, User, temp
from pyrogram.errors import FloodWait

@Client.on_message(filters.private & filters.command(["forward"]))
async def forward(client, message):
    try:
        des_ch = await client.ask(message.from_user.id, "Send Me Your Destination Channel ID (Your Database Channel ID)")
        chat_id = int(des_ch.text)
        to_channel = await User.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f"Error While Getting Destination Channel\n{str(e)}")

    try:
        fromid = await client.ask(message.from_user.id, "Forward me the last message from the SOURCE CHANNEL\n(you can also send me the link to last message)")
        if fromid.text and not fromid.forward_date:
            regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
            match = regex.match(fromid.text.replace("?single", ""))
            if not match:
                return await message.reply('Invalid link')
            chat_id = match.group(4)
            last_msg_id = int(match.group(5)) + 1
            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        elif fromid.forward_from_chat and fromid.forward_from_chat.type == enums.ChatType.CHANNEL:
            last_msg_id = int(fromid.forward_from_message_id) + 1
            chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
        from_channel = await User.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f"Error While Getting Source Channel\n{str(e)}")

    first_msg = await client.ask(message.from_user.id, "**Enter the ID of the starting message to copy**")
    first_msg_id = 2 if int(first_msg.text) < 2 else int(first_msg.text)
    start_time = time.time()
    forwarded_count = 0
    invalid_msg = 0
    skipped_msg = 0  

    k = await message.reply("Starting Forwarding...")

    for i in range(first_msg_id, last_msg_id):
        if temp.CANCEL:
            break 
        try:
            i_file = await User.get_messages(from_channel.id, i)
            
            if not i_file.media:
                invalid_msg += 1
                continue
            
            file_name = None
            file_size = None
            file_caption = i_file.caption if i_file.caption else ""

            if i_file.document:
                file_name = i_file.document.file_name
                file_size = get_size(i_file.document.file_size)
            elif i_file.video:
                file_name = i_file.video.file_name
                file_size = get_size(i_file.video.file_size)
            elif i_file.audio:
                file_name = i_file.audio.file_name
                file_size = get_size(i_file.audio.file_size)

            if not file_name or not re.search(r"s\d{1,2}[\.\s]?e[p]?\d{1,2}|season|\bepisode\b", file_name.lower()):
                skipped_msg += 1
                continue
      
            await User.copy_message(
                chat_id=to_channel.id,
                from_chat_id=from_channel.id,
                message_id=i,
                caption=CAPTION.format(file_name=file_name, file_size=file_size, file_caption=file_caption)
            )
            forwarded_count += 1

            # Add random sleep here (between 2 to 5 seconds)
            random_sleep_time = random.uniform(2, 5)
            await asyncio.sleep(random_sleep_time)

        except FloodWait as e:
            await message.reply(f"Flood Wait err Wait For {e.value + 1} Sec")
            await asyncio.sleep(e.value + 1)
        except Exception as e:
            print(f"Forwarding Stopped Due to {e}")
            return await message.reply(f"Forward Stopped at {i}\nCheck Log For More Info")

        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        try:
            await k.edit(
                f"**Forwarding in progress...**\n\n"
                f"✅ Forwarded: {forwarded_count}\n"
                f"❌ Invalid (No Media): {invalid_msg}\n"
                f"⏭️ Skipped (No Episode Format): {skipped_msg}\n"
                f"⏳ Elapsed Time: {elapsed_minutes} min"
                )
            await asyncio.sleep(4)
        except Exception as a:
            print("Cant Edit Flood Wait")
            pass

    total_time = time.time() - start_time
    total_minutes = int(total_time // 60)
    await k.edit(
        f"**Forwarding Completed!**\n\n"
        f"✅ Total Forwarded: {forwarded_count}\n"
        f"❌ Invalid Messages (No Media): {invalid_msg}\n"
        f"⏭️ Skipped (No Episode Format): {skipped_msg}\n"
        f"⏳ Total Time: {total_minutes} min"
    )

@Client.on_message(filters.private & filters.command(["cancel"]))
async def fordcancel(bot, message):
    temp.CANCEL = True
    await message.reply("Forwarding Stopped")

def get_size(size):
    """Get size in readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])
            
