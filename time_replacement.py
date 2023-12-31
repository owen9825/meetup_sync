import argparse
import datetime
import io
import re

from bs4 import BeautifulSoup

from logging_helpers import get_colored_logger

# Sample HTML content
html_content = '''
<div>
    <time class="text-[#00829B] text-sm font-medium uppercase">Sat, Nov 11, 2023, 4:00 PM UTC+11</time>
</div>
'''

logger = get_colored_logger()


def get_tzinfo(offset_str) -> datetime.timezone:
    pattern = r'([+-])(\d{1,2})(:?)(\d{0,2})'
    match = re.match(pattern, offset_str)
    if not match:
        raise ValueError("Invalid offset format")

    sign, hours, colon, minutes = match.groups()

    hours = int(hours)
    minutes = int(minutes) if minutes else 0

    # Adjust the sign of the offset
    if sign == '-':
        hours = -hours
        minutes = -minutes

    # Create timedelta object representing the offset
    offset = datetime.timedelta(hours=hours, minutes=minutes)

    # Return the tzinfo object with the specified offset
    return datetime.timezone(offset)


MEETUP_DATE_FORMAT = "%a, %b %d, %Y, %I:%M %p"


def get_datetime_from_string(time_string) -> datetime:
    parts = time_string.split("UTC")
    parsed_date = datetime.datetime.strptime(parts[0].strip(), MEETUP_DATE_FORMAT)
    return parsed_date.replace(tzinfo=get_tzinfo(offset_str=parts[1]))


def get_datetime_from_element(time_element) -> datetime.datetime:
    return get_datetime_from_string(time_string=time_element.get_text())


def replace_time_strings(source_filename: str):
    with io.open(source_filename, "w") as source_file:
        html_content = source_file.read()
        # Create a Beautiful Soup object
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the 'time' element
        for time_element in soup.find_all('time'):
            # Replace with Unix timestamp
            time_element.text = int(get_datetime_from_element(time_element).timestamp() * 1_000)
            logger(f"A time element has been replaced with {time_element.text}")
        print(source_file.write(soup.prettify()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This program searches for <time> elements in a local HTML file, and replaces strings with Unix "
                    "timestamps, ready to be converted into the user's timezone, in their browser.")
    parser.add_argument(
        "--file",
        type=str,
        help="The HTML file to overwrite",
    )
    args = parser.parse_args()
