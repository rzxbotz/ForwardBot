import re
import time
import asyncio
import random
from pyrogram import Client, filters, enums
from config import CAPTION, User, temp
from pyrogram.errors import FloodWait, ChannelPrivate, PeerIdInvalid, ChatAdminRequired

@Client.on_message(filters.private & filters.command(["forward"]))
async def forward(client, message):
    try:
        des_ch = await client.ask(message.from_user.id, "Send me your Destination Channel ID (Your Database Channel ID) or invite link:")
        dest_input = des_ch.text.strip()
        if dest_input.startswith("https://t.me/joinchat/"):
            to_channel = await client.join_chat(dest_input)
        else:
            chat_id = int(dest_input)
            to_channel = await User.get_chat(chat_id)
    except (ValueError, PeerIdInvalid):
        return await message.reply("Invalid Destination Channel ID or invite link.")
    except Exception as e:
        return await message.reply(f"Error while accessing Destination Channel:\n{str(e)}")

    try:
        fromid = await client.ask(message.from_user.id, "Forward me the last message from the SOURCE CHANNEL\n(you can also send me the link to the last message):")
        if fromid.text and not fromid.forward_date:
            regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
            match = regex.match(fromid.text.replace("?single", ""))
            if not match:
                return await message.reply('Invalid link.')
            chat_id = match.group(4)
            last_msg_id = int(match.group(5)) + 1
            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        elif fromid.forward_from_chat and fromid.forward_from_chat.type == enums.ChatType.CHANNEL:
            last_msg_id = int(fromid.forward_from_message_id) + 1
            chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
        else:
            return await message.reply('Invalid source message or link.')
        from_channel = await User.get_chat(chat_id)
    except (PeerIdInvalid, ValueError):
        return await message.reply("Invalid Source Channel ID or invite link.")
    except Exception as e:
        return await message.reply(f"Error while accessing Source Channel:\n{str(e)}")

    try:
        first_msg = await client.ask(message.from_user.id, "**Enter the ID of the starting message to copy:**")
        first_msg_id = max(2, int(first_msg.text))
    except ValueError:
        return await message.reply("Invalid message ID. Please enter a valid number.")

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

            if not file_name or not re.search(r"(s\d{1,2}[.\s]?e\d{1,2}|season\s?\d{1,2}|episode\s?\d{1,2})", file_name, re.IGNORECASE):
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
            await message.reply(f"Flood Wait: Waiting for {e.value + 1} seconds.")
            await asyncio.sleep(e.value + 1)
        except ChannelPrivate:
            await message.reply(f"ChannelPrivate Error: The channel (ID: {from_channel.id}) is private and cannot be accessed.")
            break
        except ChatAdminRequired:
            await message.reply(f"ChatAdminRequired Error: Missing admin rights in the channel (ID: {from_channel.id}).")
            break
        except Exception as e:
            await message.reply(f"An unexpected error occurred at message ID {i}:\n{str(e)}")
            break

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
            await asyncio.sleep(3)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except Exception:
            pass

    total_time = time.time() - start_time
    total_minutes = int(total_time // 60)
    await k.edit(
        f"**Forwarding Completed!**\n\n"
        f"✅ Total Forwarded: {forwarded_count}\n"
        f"❌ Invalid Messages (No Media): {invalid_msg}\n"
        f"
::contentReference[oaicite:0]{index=0}
 
