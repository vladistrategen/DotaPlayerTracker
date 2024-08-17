from datetime import datetime
import re


class RankDataParser:
    __MESSAGE_PATTERN = r"(\d{2}/\d{2}/\d{4})-(\d{2}:\d{2}:\d{2}) - Rank: (\d+)"
    __DATE_TIME_FORMAT = '%d/%m/%Y %H:%M:%S'

    @staticmethod
    def parse_message(message_content):
        match = re.match(RankDataParser.__MESSAGE_PATTERN, message_content)
        if match:
            date_str, time_str, rank = match.groups()
            date_time_str = f"{date_str} {time_str}"
            date_time = datetime.strptime(date_time_str, RankDataParser.__DATE_TIME_FORMAT)
            rank = int(rank)
            return date_time, rank
        return None, None

    @staticmethod
    def get_message_date(message_content):
        date_time, _ = RankDataParser.parse_message(message_content)
        return date_time
    