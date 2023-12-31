import argparse
import datetime
import io
import re
from typing import Optional

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


# If this is missing, either there are no events, or Meetup has changed their HTML.
RELIABLE_DIV_ID = "e-1"  # Event 1
HIDDEN_CLASS = "hidden"  # The destination website is meant to hide any element with this CSS class.
DESTINATION_ID = "eventList"  # The id in the destination file


def get_event_ul(soup) -> Optional[BeautifulSoup]:
    reliable_div = soup.find("div", id=RELIABLE_DIV_ID, recursive=True)  # This seems the most reliable
    if not reliable_div:
        logger.error("Could not find %s in this soup of %s characters", RELIABLE_DIV_ID, len(soup.text))
        return None
    ul = reliable_div.find_parent("ul")
    if not ul:
        logger.error("Element %s lacks a ul as an ancestor", RELIABLE_DIV_ID)
        return None
    return ul


def get_event_list_with_unix_times(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    event_list = get_event_ul(soup)
    if not event_list:
        return None
    times = event_list.find_all("time", recursive=True)
    for time_element in times:
        # Replace with Unix timestamp
        time_element.string.replace_with(str(int(get_datetime_from_element(time_element).timestamp() * 1_000)))
    return event_list


def parse_events_from_file(source_filename) -> Optional[BeautifulSoup]:
    with io.open(source_filename) as source_file:
        html_content = source_file.read()
    source_soup = BeautifulSoup(html_content, "html.parser")
    return get_event_list_with_unix_times(source_soup)


def hide_events(event_list: Optional[BeautifulSoup], hide_finished_events: bool,
                visible_population: Optional[int]) -> None:
    # Setting visible_population to null means that all events will be visible
    if not event_list:
        return
    event_lis = event_list.find_all("li", recursive=False)  # Only immediate children
    displayed = 0
    now_ms = datetime.datetime.utcnow().timestamp() * 1_000
    for e, event_li in enumerate(event_lis):
        event_time = event_li.find("time", recursive=True)
        if event_time:
            time_ms = int(event_time.text)
        else:
            child_div = event_li.find("div", recursive=True)
            if child_div:
                label = child_div["id"]
            else:
                label = f"element {e}"
            logger.info("No time found for event %s", label)
            time_ms = None
        if time_ms and time_ms < now_ms and hide_finished_events:
            if not event_li.get("class"):
                event_li["class"] = []
            event_li["class"].append(HIDDEN_CLASS)
        elif isinstance(visible_population, int) and displayed >= visible_population:
            if not event_li.get("class"):
                event_li["class"] = []
            event_li["class"].append(HIDDEN_CLASS)
        else:
            displayed += 1
    logger.info("%s / %s events are to be displayed", displayed, len(event_lis))


IMAGE_IDENTIFIER = "🖼"  # A reliable signal to our shell script


def log_imagery_for_copying(image_soup: BeautifulSoup):
    """
    Log all the images in this soup, so that they may be copied to the new destination. We'll leave it to a shell script
    to carry this out.
    """
    for image in image_soup.find_all("img", recursive=True):
        # Do not put a space in-between these two strings, otherwise it's more hassle to extract it.
        logger.info("%s%s", IMAGE_IDENTIFIER, image["src"])


def replace_events_in_file(source_filename: str, destination_filename, hide_finished_events: bool,
                           visible_population: int):
    # Read some events on one page, and inject a modified version into a destination file.
    events = parse_events_from_file(source_filename=source_filename)
    if not events:
        logger.warning("Events could not be parsed from %s", source_filename)
        return
    hide_events(events, hide_finished_events=hide_finished_events, visible_population=visible_population)
    if not destination_filename:
        logger.info(events.prettify("utf-8").decode())
        return
    with io.open(destination_filename, "r") as destination_file:
        html_content = destination_file.read()
    destination_soup = BeautifulSoup(html_content, "html.parser")
    destination_events = destination_soup.find("ul", id=DESTINATION_ID, recursive=True)
    if not destination_events:
        logger.error("Element %s could not be found in %s", DESTINATION_ID, destination_filename)
        return
    events["id"] = DESTINATION_ID  # We need to be able to find it again next time.
    destination_events.replace_with(events)
    with io.open(destination_filename, "w") as destination_file:
        destination_file.write(destination_soup.prettify("utf-8").decode())
    logger.info("Events have been written to %s", destination_filename)
    log_imagery_for_copying(events)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This program searches for a <ul> in a local HTML file. The constituent <time> elements in the <ul>"
                    " are replaced with Unix timestamps (so that they can be converted later when rendered), then this "
                    "revised <ul> is saved to a new file.")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="The HTML file to read, for events",
    )
    parser.add_argument(
        "--destination",
        type=str,
        required=False,
        help="The HTML file where events should be written",
    )
    parser.add_argument(
        "--visible-population",
        type=int,
        default=2,
        help="The number of events that should be visible, before 'show more' is displayed",
    )
    args = parser.parse_args()
    replace_events_in_file(source_filename=args.source, destination_filename=args.destination,
                           hide_finished_events=False, visible_population=args.visible_population)
