import lynxpresence
import pympris as mpris
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from lynxpresence import Presence, ActivityType
import time
import re
import argparse
from discord_webhook import DiscordWebhook, DiscordEmbed
import sys
import signal

version = "1.0"

parser = argparse.ArgumentParser(
    prog="richmpris",
    description="a program to display rich presence information from the MPRIS d-bus",
)

parser.add_argument("-c", "--client-id", help="override for the discord client id")
parser.add_argument(
    "-u", "--unsanitized", help="do not sanitize song metadata", action="store_true"
)
parser.add_argument(
    "-w", "--webhook-url", help="post status to a discord channel via a webhook"
)
parser.add_argument(
    "-i",
    "--image",
    help="image override; takes a web link or a discord asset string (set as 'richmpris' to lock default)",
)
parser.add_argument(
    "-o",
    "--override-webhook-image",
    help="makes the '--image' override also apply webhooks (only applies to web links)",
    action="store_true",
)
parser.add_argument(
    "-s",
    "--swap-meta",
    help="swap the title and artist fields in metadata",
    action="store_true",
)

cid = "1421374440239009824"
wlink = None
sleep_interval = 15

title_artist_separators = [
    " - ",
    " ~ ",
    " — ",
    "—",
    ": ",
    " : ",
]

blocked_phrases = [
    "(official video)",
    "[official video]",
    "(official audio)",
    "[official audio]",
    "(official music video)",
    "[official music video]",
    "official video",
    "official audio",
    "official music video",
    "(audio)",
    "[audio]",
    "(lyric video)",
    "lyric video",
    "[lyric video]",
    "(lyrics)",
    "[lyrics]",
    " - topic",
    "(official visualizer)",
    "(visualizer)",
    "[official visualizer]",
    "[visualizer]",
    "official visualizer",
]

recent_print_string = ""

signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))


def is_recent_print_unique(text=""):
    global recent_print_string
    return not text == recent_print_string


def print_unique(text=""):
    if is_recent_print_unique(text):
        global recent_print_string
        recent_print_string = text
        print(text)
        return True
    return False


def print_unique_song(app_name, artist, title, cover, post_webhook):
    text = f"""
Found song in {app_name}:
{artist} - {title}
Cover image path is {cover}
        """
    if print_unique(text):
        if post_webhook:
            webhook = DiscordWebhook(url=post_webhook)
            embed = DiscordEmbed(title=title, description=artist, color="ffffff")
            embed.set_footer("sent from richmpris")
            embed.add_embed_field(name="detected bus", value=app_name)
            embed.set_timestamp()
            if cover.startswith("http"):
                embed.set_thumbnail(url=cover)
            webhook.add_embed(embed)
            webhook.execute()


def no_source(RPC: Presence):
    RPC.clear()
    print_unique(f"""
No media source found
Rescanning in {sleep_interval} seconds
        """)


def handle_interrupt(sig, frame):
    sys.exit(0)


def sleep():
    time.sleep(sleep_interval)


def sanitize_title(title: str) -> str:
    if not title:
        return title
    orig = title
    # remove blocked phrases (case-insensitive), treat phrases literally
    for phrase in blocked_phrases:
        # build a case-insensitive literal regex
        pat = re.compile(re.escape(phrase), flags=re.I)
        orig = pat.sub("", orig)
    # remove leftover brackets/parentheses that are empty or whitespace-only, e.g. "Song ()"
    orig = re.sub(r"[$$$\{]\s*[$$$\}]", "", orig)
    # collapse multiple spaces and trim surrounding punctuation/spaces
    orig = re.sub(r"\s{2,}", " ", orig).strip()
    orig = re.sub(r"^[\-\:\|\s]+|[\-\:\|\s]+$", "", orig)
    # collapse repeated punctuation like "Song - " => "Song"
    orig = orig.strip(" -:|")
    return orig.strip()


def main(args):
    RPC = Presence(cid)
    try:
        RPC.connect()
    except lynxpresence.exceptions.DiscordNotFound:
        print("no client available")
        sys.exit(1)

    while True:
        dbus_loop = DBusGMainLoop()
        bus = dbus.SessionBus(mainloop=dbus_loop)

        player_ids = list(mpris.available_players())

        if not player_ids:
            no_source(RPC)
            sleep()
            continue

        mp = mpris.MediaPlayer(player_ids[-1], bus)

        # metadata stuff
        app_name = mp.root.Identity
        meta = mp.player.Metadata
        title = meta.get("xesam:title") if "xesam:title" in meta else "N/A"
        artist = meta.get("xesam:artist") if "xesam:artist" in meta else "N/A"
        if not isinstance(artist, str):  # sometimes this field is an array
            artist = artist[0]
        cover = (
            meta.get("mpris:artUrl").replace(
                "file://",
                "",  # this does not work as intended. might revisit later
            )
            if "mpris:artUrl" in meta
            else "N/A"
        )

        # sanitize title/artist (remove blocked phrases etc.)
        if not args.unsanitized:
            if isinstance(title, str) and title.lower() != "n/a":
                title = sanitize_title(title)
            if isinstance(artist, str) and artist.lower() != "n/a":
                artist = sanitize_title(artist)

            # dynamic metadata detection
            if any(pattern in title for pattern in title_artist_separators):
                new = ""
                for separator in title_artist_separators:
                    if separator in title:
                        new = title.split(separator, 1)
                        break
                if new:
                    artist = new[0].strip()
                    title = new[1].strip()

        if not title == "N/A":
            # clean
            title = title.strip()
            artist = artist.strip()
            pcover = "richmpris" if not cover.startswith("http") else cover
            if args.image:
                pcover = args.image
            if args.override_webhook_image:
                cover = pcover if pcover.startswith("http") else cover
            if args.swap_meta:
                title, artist = artist, title

            RPC.update(
                activity_type=ActivityType.LISTENING,
                state=artist,
                details=title,
                large_image=pcover,
            )

            print_unique_song(app_name, artist, title, cover, args.webhook_url)
        else:
            no_source(RPC)

        sleep()


if __name__ == "__main__":
    args = parser.parse_args()
    if "client_id" in args:
        cid = args.client_id if not args.client_id == None else cid
    print(f"running richmpris version {version}")
    main(args)
