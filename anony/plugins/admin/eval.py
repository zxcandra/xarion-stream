# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import io
import sys
import traceback

from pyrogram import enums, filters, types

from anony import app


@app.on_message(filters.command(["eval", "exec"]) & app.sudoers)
async def eval_cmd(_, message: types.Message):
    """Execute Python code (Sudo only)."""
    
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "ℹ️ <b>Penggunaan Eval</b>\n\n<blockquote><code>/eval [code]</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    code = message.text.split(None, 1)[1] if len(message.command) > 1 else message.reply_to_message.text
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    
    try:
        exec(code)
        output = redirected_output.getvalue() or "Success"
    except Exception:
        output = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    await message.reply_text(
        f"💻 <b>Eval Output</b>\n\n<pre>{output}</pre>",
        parse_mode=enums.ParseMode.HTML
    )
