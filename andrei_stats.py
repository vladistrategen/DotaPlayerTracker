import discord
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dotenv import load_dotenv
import os
import argparse
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

intents = discord.Intents.default()
intents.messages = True

client = discord.Client(intents=intents)

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
    plt.ylim(0, 1000)  # Set y-axis limits

    if inverted:
        plt.gca().invert_yaxis()
    
    # Save the plot as an image
    image_path = f'{"inverted_" if inverted else "normal_"}{"detailed_" if detailed else ""}rank_evolution.png'
    plt.savefig(image_path, dpi=100)
    plt.close()
    
    return image_path

def create_animation(df, inverted=False, detailed=False, duration=10):
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    line, = ax.plot([], [], linestyle='-', marker='')
    text = ax.text(0.5, 0.9, '', transform=ax.transAxes, ha='center')
    progress_bar = tqdm(total=len(df), desc="Creating animation frames")
    min_points = []
    max_points = []
    
    def init():
        ax.set_xlim(df['DateTime'].min(), df['DateTime'].max())
        ax.set_ylim(0, 1000)  # Fixed y-axis range
        ax.grid(True)  # Add grid lines
        if inverted:
            ax.invert_yaxis()
        return line, text

    def update(frame):
        current_time = df['DateTime'].iloc[frame]
        text.set_text(current_time.strftime('%B %Y'))
        xdata = df['DateTime'].iloc[:frame + 1]
        ydata = df['Rank'].iloc[:frame + 1]
        line.set_data(xdata, ydata)
        
        if detailed:
            current_month = df['DateTime'].dt.to_period('M').iloc[frame]
            month_group = df[df['DateTime'].dt.to_period('M') == current_month]
            if not month_group.empty:
                max_rank = month_group.loc[month_group['Rank'].idxmin()]
                min_rank = month_group.loc[month_group['Rank'].idxmax()]
                if current_time >= min_rank['DateTime']:
                    min_points.append((min_rank['DateTime'], min_rank['Rank']))
                if current_time >= max_rank['DateTime']:
                    max_points.append((max_rank['DateTime'], max_rank['Rank']))
            for min_point in min_points:
                ax.scatter(min_point[0], min_point[1], color='blue')
                ax.text(min_point[0], min_point[1], f"{min_point[1]}", verticalalignment='top', horizontalalignment='right', color='red')
            for max_point in max_points:
                ax.scatter(max_point[0], max_point[1], color='green')
                ax.text(max_point[0], max_point[1], f"{max_point[1]}", verticalalignment='bottom', horizontalalignment='left', color='green')
        
        progress_bar.update(1)
        return line, text

    fps = len(df) / duration
    anim = FuncAnimation(fig, update, frames=len(df), init_func=init, blit=False, repeat=False)
    
    # Save the animation as a video
    video_path = f'{"inverted_" if inverted else "normal_"}{"detailed_" if detailed else ""}rank_evolution.mp4'
    anim.save(video_path, writer='ffmpeg', fps=fps, dpi=100)
    progress_bar.close()
    plt.close(fig)
    
    return video_path

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    
    # Read all messages from the channel
    messages = []
    last_message_id = None
    while True:
        new_messages = []
        async for message in channel.history(limit=100, before=discord.Object(id=last_message_id) if last_message_id else None):
            new_messages.append(message)
        
        if not new_messages:
            print("No more messages found.")
            break
        
        date_times = [message.created_at for message in new_messages]
        date1 = date_times[0].strftime('%Y-%m-%d')
        date2 = date_times[-1].strftime('%Y-%m-%d')
        print(f'Found {len(new_messages)} messages between {date1} and {date2}')
        
        messages.extend(new_messages)
        last_message_id = new_messages[-1].id
    
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
            message = await channel.send(content=f"Rank evolution animation generated on {today_str}", file=discord.File(video_path))
        else:
            image_path = plot_rank_evolution(df, args.inverted, args.detailed)
            today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = await channel.send(content=f"Rank evolution plot generated on {today_str}", file=discord.File(image_path))
        
        if args.pin:
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
    args = parser.parse_args()
    
    asyncio.run(main())
