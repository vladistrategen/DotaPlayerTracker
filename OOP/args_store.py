import argparse
import os
from dotenv import load_dotenv

class ARGS:
    """Parent class to manage arguments and environment variables."""

    class CLIArgs:
        """Subclass to handle command-line arguments."""
        inverted = False
        detailed = False
        video = False
        duration = 10
        start_date = None
        end_date = None
        pin = False
        send = False
        zoomed_in = False

        @staticmethod
        def load_args():
            parser = argparse.ArgumentParser(description="Plot Rank Evolution")
            parser.add_argument('--inverted', '-i', action='store_true', help="Plot the graph in reverse")
            parser.add_argument('--detailed', '-d', action='store_true', help="Plot the graph with local min and max for each month")
            parser.add_argument('--video', '-v', action='store_true', help="Create an animation of the rank evolution")
            parser.add_argument('--duration', '-t', type=int, default=10, help="Duration of the animation in seconds")
            parser.add_argument('--pin', '-p', action='store_true', help="Pin the generated plot")
            parser.add_argument('--send', '-s', action='store_true', help="Send the generated plot")
            parser.add_argument('--start_date', '-sd', type=str, help='Start date for the data collection')
            parser.add_argument('--end_date', '-ed', type=str, help='End date for the data collection')
            parser.add_argument('--zoomed_in', '-z', action='store_true', help='Plot the graph with a dynamic, zoomed in y-axis')

            args = parser.parse_args()

            ARGS.CLIArgs.inverted = args.inverted
            ARGS.CLIArgs.detailed = args.detailed
            ARGS.CLIArgs.video = args.video
            ARGS.CLIArgs.duration = args.duration
            ARGS.CLIArgs.start_date = args.start_date
            ARGS.CLIArgs.end_date = args.end_date
            ARGS.CLIArgs.pin = args.pin
            ARGS.CLIArgs.send = args.send
            ARGS.CLIArgs.zoomed_in = args.zoomed_in

    class EnvVars:
        """Subclass to handle environment variables."""
        channel_id = None
        country_code = None
        discord_bot_token = None
        player_id = None
        player_name = None
        team_id = None
        team_tag = None
        webhook_url_chat = None
        webhook_url_log = None

        @staticmethod
        def load_env_vars():
            load_dotenv()  # Load variables from .env file if present

            ARGS.EnvVars.channel_id = os.getenv('CHANNEL_ID')
            ARGS.EnvVars.country_code = os.getenv('COUNTRY_CODE')
            ARGS.EnvVars.discord_bot_token = os.getenv('DISCORD_BOT_TOKEN')
            ARGS.EnvVars.player_id = os.getenv('PLAYER_ID')
            ARGS.EnvVars.player_name = os.getenv('PLAYER_NAME')
            ARGS.EnvVars.team_id = os.getenv('TEAM_ID')
            ARGS.EnvVars.team_tag = os.getenv('TEAM_TAG')
            ARGS.EnvVars.webhook_url_chat = os.getenv('WEBHOOK_URL_CHAT')
            ARGS.EnvVars.webhook_url_log = os.getenv('WEBHOOK_URL_LOG')

    @staticmethod
    def load_all():
        ARGS.CLIArgs.load_args()
        ARGS.EnvVars.load_env_vars()
