import sys
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Telegram, Logging


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, Logging.LEVEL.upper()),
        format=Logging.FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def load_plugins(plugins_dir: str = "plugins") -> List[Router]:
    import importlib.util
    
    plugins_path = Path(plugins_dir).resolve()
    routers: List[Router] = []
    
    if not plugins_path.exists():
        plugins_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created plugins directory: {plugins_dir}")
        return routers
    
    if str(plugins_path.parent) not in sys.path:
        sys.path.insert(0, str(plugins_path.parent))
    
    for file_path in plugins_path.glob("*.py"):
        if file_path.name.startswith("_"):
            continue
        
        spec = importlib.util.spec_from_file_location(
            f"{plugins_dir}.{file_path.stem}",
            file_path
        )
        
        if spec and spec.loader:
            try:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, 'router') and isinstance(module.router, Router):
                    routers.append(module.router)
                    logger.info(f"✅ Loaded plugin: {file_path.stem}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load {file_path.stem}: {e}")
    
    return routers


async def show_startup_info(bot: Bot):
    me = await bot.me()
    
    print("\n" + "=" * 50)
    print("🤖 BOT IS RUNNING")
    print("=" * 50)
    print(f"Name:     {me.full_name}")
    print(f"Username: @{me.username}")
    print(f"ID:       {me.id}")
    print(f"Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Plugins:  {len([p for p in Path('plugins').glob('*.py') if not p.name.startswith('_')])}")
    print("=" * 50 + "\n")
    
    logger.info(f"Bot @{me.username} started successfully")


async def main():
    global logger
    logger = setup_logging()
    
    bot = Bot(
        token=Telegram.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    routers = load_plugins("plugins")
    for router in routers:
        dp.include_router(router)
    
    await show_startup_info(bot)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
