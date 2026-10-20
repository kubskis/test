"""Тестовый бот + сайт. Нужен только чтобы проверить, что домен и сайт работают на хостинге.

Переменные окружения:
  BOT_TOKEN  — токен тестового бота от @BotFather (ОБЯЗАТЕЛЬНО хранить только в переменных хостинга)
  PORT       — порт веб-сервера (по умолчанию 3000, как в настройках домена)
  SITE_URL   — адрес сайта для сообщения бота (необязательно), например https://towerofsecrets.run.place
"""
import asyncio
import logging
import os
import re
import time

from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
PORT = int(os.getenv("PORT", "3000"))
SITE_URL = (os.getenv("SITE_URL") or "").strip()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STARTED_AT = time.time()
STATE = {"bot": "not_started"}   # not_started | up | error


# ---------- сайт ----------
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
# Сайт: страницы и файлы лежат рядом с main.py. Отдаём только безопасные расширения (код .py, .txt, .jpg бота не отдаём).
_SITE_EXT = {".html", ".css", ".js", ".svg", ".ico", ".png", ".webp"}
_SITE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}(\.[A-Za-z0-9]{2,5})?$")

def _site_file(name: str):
    """'rules' -> rules.html, 'style.css' -> style.css. Возвращает путь или None."""
    if not _SITE_NAME_RE.match(name):
        return None
    base, ext = os.path.splitext(name)
    fname = base + ".html" if not ext else name
    if os.path.splitext(fname)[1].lower() not in _SITE_EXT:
        return None
    path = os.path.join(SITE_DIR, fname)
    return path if os.path.isfile(path) else None

async def _site_404():
    page = os.path.join(SITE_DIR, "404.html")
    if os.path.isfile(page):
        return web.FileResponse(page, status=404, headers={"Cache-Control": "no-cache"})
    return web.Response(status=404, text="404 — страница не найдена")

async def handle_index(request):
    """Главная."""
    path = _site_file("index")
    if path:
        return web.FileResponse(path, headers={"Cache-Control": "no-cache"})
    return web.Response(text="index.html не найден")

async def handle_page(request):
    """Остальные страницы и файлы сайта: /rules, /privacy, /style.css ..."""
    path = _site_file(request.match_info["name"])
    if path:
        return web.FileResponse(path, headers={"Cache-Control": "no-cache"})
    return await _site_404()

async def handle_health(request):
    return web.Response(text="ok")


async def handle_status(request):
    return web.json_response(
        {"ok": True, "bot": STATE["bot"], "uptime": int(time.time() - STARTED_AT)},
        headers={"Cache-Control": "no-store"},
    )


@web.middleware
async def log_requests(request, handler):
    """Пишем в лог каждый запрос к сайту: так видно, доходит ли трафик до бота."""
    try:
        resp = await handler(request)
        logging.info("WEB %s %s -> %s", request.method, request.path, resp.status)
        return resp
    except web.HTTPException as e:
        logging.info("WEB %s %s -> %s", request.method, request.path, e.status)
        raise


async def start_web():
    app = web.Application(middlewares=[log_requests])
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/{name}", handle_page)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    logging.info("Сайт запущен на порту %s", PORT)


# ---------- бот ----------
async def run_bot():
    if not BOT_TOKEN:
        STATE["bot"] = "error"
        logging.error("Нет переменной BOT_TOKEN — бот не запущен, но сайт работает.")
        return
    from aiogram import Bot, Dispatcher, Router
    from aiogram.filters import CommandStart
    from aiogram.types import Message

    router = Router()

    @router.message(CommandStart())
    async def start(m: Message):
        text = "✅ Тестовый бот работает."
        if SITE_URL:
            text += f"\nСайт: {SITE_URL}"
        await m.answer(text)

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        me = await bot.get_me()
        await bot.delete_webhook(drop_pending_updates=False)
        STATE["bot"] = "up"
        logging.info("Бот @%s запущен", me.username)
        await dp.start_polling(bot)
    except Exception:
        STATE["bot"] = "error"
        logging.exception("Бот не запустился (сайт продолжает работать)")


async def main():
    await start_web()          # сначала сайт, чтобы он жил независимо от бота
    await run_bot()
    while True:                # если бота нет, сайт всё равно держим
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
