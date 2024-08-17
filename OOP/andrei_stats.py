from args_store import ARGS
from rank_evolution.discord_bot import DiscordBot

async def main():
    ARGS.load_all()
    bot = DiscordBot(ARGS.EnvVars.discord_bot_token, ARGS.EnvVars.channel_id)
    await bot.start()

if __name__ == "__main__":
    main()