"""
S10e Media Node — Discord Bot (3단계)

지원 명령:
  /mp3 <url>   슬래시 커맨드 (즉시 사용 가능)
  !mp3 <url>   프리픽스 커맨드 (Portal MESSAGE CONTENT INTENT 인증 후 활성화)

설계 원칙: 이 파일은 core.py의 download_mp3()만 호출하며,
다운로드 로직을 절대 중복 구현하지 않는다.

실행:
    python -m app.discord_bot.bot
"""
import os
import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from app.common.config import (
    DISCORD_TOKEN,
    FLASK_PORT,
    LOG_PATH,
)
from app.downloader.core import download_mp3, DownloadResult

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [bot] %(message)s",
)
logger = logging.getLogger(__name__)

# --- 설정 -----------------------------------------------------------------
COMMAND_PREFIX     = "!mp3"
ATTACH_LIMIT_BYTES = 8 * 1024 * 1024
PUBLIC_HOST        = os.environ.get("PUBLIC_HOST", "118.32.140.85")
EDIT_INTERVAL      = 1.5
GUILD_ID           = 993373094435639357  # 어피치님의 봇테스트서버

_download_sema = asyncio.Semaphore(1)

intents = discord.Intents.default()


# --- Bot 클래스 (setup_hook으로 슬래시 커맨드 등록) -----------------------
class S10eBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

    async def setup_hook(self):
        """로그인 직후, on_ready 전에 호출 — 슬래시 커맨드 등록에 적합."""
        guild = discord.Object(id=GUILD_ID)

        @self.tree.command(
            name="mp3",
            description="YouTube URL을 MP3로 다운로드합니다",
        )
        @app_commands.describe(url="YouTube URL (youtube.com / youtu.be / shorts)")
        async def slash_mp3(interaction: discord.Interaction, url: str):
            url = url.strip("<>")
            logger.info(f"/mp3 요청: {url} (by {interaction.user})")
            await interaction.response.defer(thinking=True)
            status_msg = await interaction.followup.send(
                f"⏳ 대기 중… `{url}`", wait=True
            )
            await _run_download(url, status_msg, interaction.channel)

        self.tree.copy_global_to(guild=guild)
        try:
            synced = await self.tree.sync(guild=guild)
            logger.info(f"슬래시 커맨드 {len(synced)}개 길드 동기화 완료")
            print(f"[bot] 슬래시 커맨드 등록: /{', /'.join(c.name for c in synced)}")
        except discord.Forbidden:
            logger.warning("슬래시 커맨드 등록 실패 (Missing Access) — 봇은 계속 실행됩니다.")
            print("[bot] ⚠️ 슬래시 커맨드 등록 실패 — 봇은 계속 실행 중")
        except Exception as e:
            logger.error(f"슬래시 커맨드 동기화 오류: {e}")
            print(f"[bot] ⚠️ 슬래시 커맨드 동기화 오류: {e}")

    async def on_ready(self):
        logger.info(f"로그인: {self.user} (id={self.user.id})")
        print(f"[bot] 로그인 완료: {self.user}")


bot = S10eBot()


# --- 유틸 -----------------------------------------------------------------
def _public_link(filepath: str) -> str:
    return f"http://{PUBLIC_HOST}:{FLASK_PORT}/files/{os.path.basename(filepath)}"

def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"

def _render(stage: str, url: str) -> str:
    if stage == "analyzing":
        return f"🔍 분석 중… `{url}`"
    if stage.startswith("downloading:"):
        return f"⬇️ 다운로드 중 {stage.split(':',1)[1]} `{url}`"
    if stage == "converting":
        return f"🎚️ MP3 변환 중… `{url}`"
    if stage == "duplicate":
        return f"♻️ 기존 파일 반환 `{url}`"
    if stage == "queued":
        return f"⏳ 대기 중… `{url}`"
    return f"… {stage}"


# --- 핵심 다운로드 로직 (슬래시·프리픽스 공유) ----------------------------
async def _run_download(url: str, status_msg: discord.Message, reply_channel):
    state = {"stage": "queued", "dirty": True}

    def on_progress(stage: str):
        state["stage"] = stage
        state["dirty"] = True

    async def _watcher():
        last = ""
        try:
            while True:
                if state["dirty"]:
                    text = _render(state["stage"], url)
                    if text != last:
                        try:
                            await status_msg.edit(content=text)
                            last = text
                        except discord.HTTPException:
                            pass
                    state["dirty"] = False
                await asyncio.sleep(EDIT_INTERVAL)
        except asyncio.CancelledError:
            return

    async with _download_sema:
        watcher = asyncio.create_task(_watcher())
        try:
            result: DownloadResult = await asyncio.to_thread(
                download_mp3, url, on_progress
            )
        finally:
            watcher.cancel()
            try:
                await watcher
            except Exception:
                pass

    if not result.success:
        await status_msg.edit(content=f"❌ 실패: {result.error}")
        logger.warning(f"실패: {result.error}")
        return

    title    = result.title or "다운로드 완료"
    filepath = result.filepath
    size     = os.path.getsize(filepath) if filepath and os.path.isfile(filepath) else 0

    if size and size <= ATTACH_LIMIT_BYTES:
        try:
            await reply_channel.send(
                content=f"✅ **{title}** ({_human_size(size)})",
                file=discord.File(filepath),
            )
            await status_msg.delete()
            logger.info(f"완료(첨부): {title} ({_human_size(size)})")
            return
        except discord.HTTPException as e:
            logger.warning(f"첨부 실패, 링크 폴백: {e}")

    await status_msg.edit(
        content=f"✅ **{title}** ({_human_size(size)})\n🔗 {_public_link(filepath)}"
    )
    logger.info(f"완료(링크): {title} ({_human_size(size)})")


# --- 프리픽스 커맨드 (!mp3) -----------------------------------------------
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    content = message.content.strip()
    if not content.startswith(COMMAND_PREFIX):
        return

    parts = content.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.channel.send(
            "사용법: `!mp3 <YouTube URL>`\n예: `!mp3 https://youtu.be/dQw4w9WgXcQ`"
        )
        return

    url = parts[1].strip().strip("<>")
    logger.info(f"!mp3 요청: {url} (by {message.author})")
    status_msg = await message.channel.send(f"⏳ 대기 중… `{url}`")
    await _run_download(url, status_msg, message.channel)


# --- 진입점 ---------------------------------------------------------------
def main():
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN이 없습니다. config/settings.env를 확인하세요.")
    bot.run(DISCORD_TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
