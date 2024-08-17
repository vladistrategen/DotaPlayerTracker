import discord
import re
from datetime import datetime
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dotenv import load_dotenv
import os
import argparse
from tqdm import tqdm

# Load environment variables from .env file
matplotlib.use('Agg')  # Non-interactive backend
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

if not os.path.exists('videos'):
    os.makedirs('videos')

if not os.path.exists('images'):
    os.makedirs('images')

async def fetch_messages(channel, start_date, end_date):
    messages = []
    last_message_id = None
    while True:
        new_messages = []
        async for message in channel.history(limit=100, before=discord.Object(id=last_message_id) if last_message_id else None):
            new_messages.append(message)

        if not new_messages:
            print("No more messages found.")
            break

        found_new_messages_between_dates = False

        for message in new_messages:
            message_date = parse_message(message.content)[0]
            if message_date and (not start_date or message_date >= start_date) and (not end_date or message_date <= end_date):
                found_new_messages_between_dates = True
                messages.append(message)

        # Check the dates of the first and last messages in the new batch
        first_message_date = parse_message(new_messages[0].content)[0]
        last_message_date = parse_message(new_messages[-1].content)[0]

        print(f'Searching between {first_message_date} and {last_message_date}...')
        if found_new_messages_between_dates:
            print(f'Found {len(new_messages)} messages between {first_message_date} and {last_message_date}')

        last_message_id = new_messages[-1].id
        if start_date and last_message_date < start_date:
            print("Reached messages older than the start date. Stopping...")
            break  # Stop if we've reached messages older than the start date

    return messages

# Function to parse date, time, and rank from message content
def parse_message(message_content):
    match = re.match(r"(\d{2}/\d{2}/\d{4})-(\d{2}:\d{2}:\d{2}) - Rank: (\d+)", message_content)
    if match:
        date_str, time_str, rank = match.groups()
        date_time_str = f"{date_str} {time_str}"
        date_time = datetime.strptime(date_time_str, '%d/%m/%Y %H:%M:%S')
        rank = int(rank)
        return date_time, rank
    return None, None

# Function to plot rank evolution over time
def plot_rank_evolution(df, inverted=False, detailed=False):
    plt.figure(figsize=(19.2, 10.8))
    plt.plot(df['DateTime'], df['Rank'], linestyle='-', marker='')

    # Highlight the first and last dates
    first_date = df['DateTime'].iloc[0]
    last_date = df['DateTime'].iloc[-1]
    plt.scatter([first_date, last_date], 
                [df['Rank'].iloc[0], df['Rank'].iloc[-1]], 
                color='orange')
    plt.text(first_date, df['Rank'].iloc[0], first_date.strftime('%Y-%m-%d'), verticalalignment='bottom', horizontalalignment='right', color='orange')
    plt.text(last_date, df['Rank'].iloc[-1], last_date.strftime('%Y-%m-%d'), verticalalignment='bottom', horizontalalignment='right', color='orange')

    if detailed:
        # Highlight local minimum and maximum for each month
        df['Month'] = df['DateTime'].dt.to_period('M').apply(lambda r: r.start_time)
        for month, group in df.groupby('Month'):
            if len(group) > 1:
                max_rank = group.loc[group['Rank'].idxmin()]
                min_rank = group.loc[group['Rank'].idxmax()]
                plt.scatter([min_rank['DateTime']], [min_rank['Rank']], color='red')
                plt.text(min_rank['DateTime'], min_rank['Rank'], f"{min_rank['Rank']}", verticalalignment='top', horizontalalignment='right', color='red')
                plt.scatter([max_rank['DateTime']], [max_rank['Rank']], color='green')
                plt.text(max_rank['DateTime'], max_rank['Rank'], f"{max_rank['Rank']}", verticalalignment='bottom', horizontalalignment='left', color='green')

    plt.xlabel('Date and Time')
    plt.ylabel('Rank')
    plt.title('Rank Evolution Over Time')
    plt.grid(True)
    plt.xticks(rotation=45)
    if args.zoomed_in: # TODO: fix for values close to factors of 25
        min_rank = df['Rank'].min()
        max_rank = df['Rank'].max()
        min_rank = 25 * (min_rank // 25)
        max_rank = 25 * (max_rank // 25 + 1)
        plt.ylim(min_rank, max_rank)
    else:
        plt.ylim(0, 1000)  # Set y-axis limits

    if inverted:
        plt.gca().invert_yaxis()
    
    # Save the plot as an image
    image_path = f'images/{"GENERAL" if not args.start_date and not args.end_date else ( f"{args.start_date}___{args.end_date}" if args.start_date and args.end_date else f"FROM___{args.start_date}" if args.start_date else f"UNTIL___{args.end_date}")}___{"inverted_" if inverted else "normal_"}{"detailed_" if detailed else ""}{"zoomed_in_" if args.zoomed_in else ""}rank_evolution.png'
    plt.savefig(image_path, dpi=100)
    plt.close()
    
    return image_path

def create_animation(df, inverted=False, detailed=False, duration=10):
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    line, = ax.plot([], [], linestyle='-', marker='')
    text = ax.text(0.5, 1.05, '', transform=ax.transAxes, ha='center', fontsize=15)
    progress_bar = tqdm(total=len(df), desc="Creating animation frames")
    plotted_min_points = set()
    plotted_max_points = set()

    # Get the first and last date for annotations
    first_date = df['DateTime'].iloc[0]
    last_date = df['DateTime'].iloc[-1]

    def init():
        ax.set_xlim(df['DateTime'].min(), df['DateTime'].max())
        if args.zoomed_in: # TODO: fix for values close to factors of 25
            min_rank = df['Rank'].min()
            max_rank = df['Rank'].max()
            min_rank = 25 * (min_rank // 25)
            max_rank = 25 * (max_rank // 25 + 1)
            ax.set_ylim(min_rank, max_rank)
            pass
        else:
            ax.set_ylim(0, 1000)

        ax.grid(True)  # Add grid lines

        # Add annotations for the first and last dates
        ax.annotate(first_date.strftime('%d %B %Y'), xy=(first_date, 0), xycoords=('data', 'axes fraction'),
                    xytext=(0, -30), textcoords='offset points', ha='center', fontsize=10, color='blue')
        ax.annotate(last_date.strftime('%d %B %Y'), xy=(last_date, 0), xycoords=('data', 'axes fraction'),
                    xytext=(0, -30), textcoords='offset points', ha='center', fontsize=10, color='blue')

        if inverted:
            ax.invert_yaxis()
        return line, text

    def update(frame):
        # print(f"Processing frame {frame}/{len(df)}")  
        current_time = df['DateTime'].iloc[frame]
        current_rank = df['Rank'].iloc[frame]
        text.set_text(f"{current_time.strftime('%d %B %Y, %H:%M')}, Rank: {current_rank}")
        xdata = df['DateTime'].iloc[:frame + 1]
        ydata = df['Rank'].iloc[:frame + 1]
        line.set_data(xdata, ydata)

        if detailed: # TODO: add option to select min/max interval
            current_month = df['DateTime'].dt.to_period('M').iloc[frame]
            month_group = df[df['DateTime'].dt.to_period('M') == current_month]

            if not month_group.empty:
                max_rank = month_group.loc[month_group['Rank'].idxmin()]
                min_rank = month_group.loc[month_group['Rank'].idxmax()]

                if (current_month, min_rank['DateTime']) not in plotted_min_points and current_time >= min_rank['DateTime']:
                    ax.scatter(min_rank['DateTime'], min_rank['Rank'], color='blue')
                    ax.text(min_rank['DateTime'], min_rank['Rank'], f"{min_rank['Rank']}", verticalalignment='top', horizontalalignment='right', color='red')
                    plotted_min_points.add((current_month, min_rank['DateTime']))

                if (current_month, max_rank['DateTime']) not in plotted_max_points and current_time >= max_rank['DateTime']:
                    ax.scatter(max_rank['DateTime'], max_rank['Rank'], color='green')
                    ax.text(max_rank['DateTime'], max_rank['Rank'], f"{max_rank['Rank']}", verticalalignment='bottom', horizontalalignment='left', color='green')
                    plotted_max_points.add((current_month, max_rank['DateTime']))

        progress_bar.update(1)
        return line, text

    fps = len(df) / duration
    anim = FuncAnimation(fig, update, frames=len(df), init_func=init, blit=False, repeat=False)

    # Save the animation as a video
    video_path = f'videos/{"GENERAL" if not args.start_date and not args.end_date else ( f"{args.start_date}___{args.end_date}" if args.start_date and args.end_date else f"FROM___{args.start_date}" if args.start_date else f"UNTIL___{args.end_date}")}___{"inverted_" if inverted else "normal_"}{"detailed_" if detailed else ""}{"zoomed_in_" if args.zoomed_in else ""}rank_evolution.mp4'
    anim.save(video_path, writer='ffmpeg', fps=fps, dpi=100, extra_args=['-v', 'error'])
    progress_bar.close()
    plt.close(fig)
    
    return video_path


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    
    global args  # Make sure args are globally accessible within async functions
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None
    messages = await fetch_messages(channel, start_date, end_date)
    
    data = []
    for message in messages:
        date_time, rank = parse_message(message.content)
        if date_time and rank is not None:
            data.append((date_time, rank))

    if data:
        df = pd.DataFrame(data, columns=['DateTime', 'Rank'])
        df.sort_values(by='DateTime', inplace=True)
        
        if args.video:
            video_path = create_animation(df, args.inverted, args.detailed, args.duration)
            today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if args.send:
                message = await channel.send(content=f"Rank evolution animation generated on {today_str}", file=discord.File(video_path))
        else:
            image_path = plot_rank_evolution(df, args.inverted, args.detailed)
            today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if args.send:
                message = await channel.send(content=f"Rank evolution plot generated on {today_str}", file=discord.File(image_path))
        
        if args.pin and args.send:
            await message.pin()
    
    await client.close()

async def main():
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    
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
    
    asyncio.run(main())
