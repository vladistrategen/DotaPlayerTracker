from datetime import datetime
import re
import discord
import pandas as pd
from args_store import ARGS
from . import rank_data_parser
from rank_evolution.Plotter.plotter_manager import PlotterFactory

class DiscordBot:
    def __init__(self, token, channel_id):
        self.__token = token
        self.__channel_id = int(channel_id)
        __intents = discord.Intents.default()
        __intents.messages = True
        __intents.message_content = True
        self.__client = discord.Client(intents=__intents)
        self.__channel = None

        # Register events after the client is created
        self.__client.event(self.on_ready)

    async def on_ready(self):
        print(f'Logged in as {self.__client.user}')

        start_date = datetime.strptime(ARGS.CLIArgs.start_date, '%Y-%m-%d') if ARGS.CLIArgs.start_date else None
        end_date = datetime.strptime(ARGS.CLIArgs.end_date, '%Y-%m-%d') if ARGS.CLIArgs.end_date else None
        self.__channel = self.__client.get_channel(self.__channel_id)
        messages = await self.fetch_messages(start_date, end_date)
        today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


        data = []
        for message in messages:
            date_time, rank = rank_data_parser.parse_message(message.content)
            if date_time and rank is not None:
                data.append((date_time, rank))

        if data:
            df = pd.DataFrame(data, columns=['DateTime', 'Rank'])
            df.sort_values(by='DateTime', inplace=True)
        else:
            await self.__client.close()
            raise RuntimeError("Couldn't fetch data")

        plotter = PlotterFactory.create_plotter(df)
        plotter.plot_and_save()

        if ARGS.CLIArgs.send:
            message = await self.__channel.send(content=f"Rank evolution {"animation" if ARGS.CLIArgs.video else "plot"} generated on {today_str}", file=discord.File(plotter.save_file_path))

        if ARGS.CLIArgs.pin and ARGS.CLIArgs.send:
            await message.pin()
    
        await self.__client.close()

    async def fetch_messages(self, start_date, end_date):
        messages = []
        last_message_id = None
        while True:
            new_messages = []
            async for message in self.__channel.history(limit=100, before=discord.Object(id=last_message_id) if last_message_id else None):
                new_messages.append(message)

            if not new_messages:
                print("No more messages found.")
                break

            found_new_messages_between_dates = False

            for message in new_messages:
                message_date = rank_data_parser.get_message_date(message.content)
                if message_date and (not start_date or message_date >= start_date) and (not end_date or message_date <= end_date):
                    found_new_messages_between_dates = True
                    messages.append(message)

            # Check the dates of the first and last messages in the new batch
            first_message_date = rank_data_parser.get_message_date(new_messages[0].content)
            last_message_date = rank_data_parser.get_message_date(new_messages[-1].content)

            print(f'Searching between {first_message_date} and {last_message_date}...')
            if found_new_messages_between_dates:
                print(f'Found {len(new_messages)} messages between {first_message_date} and {last_message_date}')

            last_message_id = new_messages[-1].id
            if start_date and last_message_date < start_date:
                print("Reached messages older than the start date. Stopping...")
                break  # Stop if we've reached messages older than the start date

        return messages

    async def start(self):
        async with self.__client:
            await self.__client.start(self.__token)