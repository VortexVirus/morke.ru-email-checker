import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    LOGIN_PAGE,
    LOGIN_POST,
    INBOX_URL,
    USERNAME,
    PASSWORD,
    PROXIES,
    COOKIE_FILE,
)


# ============================================================
# Message object
# ============================================================

@dataclass
class MailMessage:
    id: int
    sender: str
    subject: str
    date: str
    url: str


# ============================================================
# SquirrelMail
# ============================================================

class SquirrelMail:

    def __init__(self):

        self.session = requests.Session()

        self.session.proxies = PROXIES

        self.session.headers.update({
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

        self.load_cookies()

    # --------------------------------------------------------

    def save_cookies(self):

        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(self.session.cookies, f)

    # --------------------------------------------------------

    def load_cookies(self):

        path = Path(COOKIE_FILE)

        if not path.exists():
            return

        with open(path, "rb") as f:
            self.session.cookies.update(
                pickle.load(f)
            )

    # --------------------------------------------------------

    def clear_cookies(self):

        self.session.cookies.clear()

        path = Path(COOKIE_FILE)

        if path.exists():
            path.unlink()

    # --------------------------------------------------------

    def get(self, url):

        r = self.session.get(
            url,
            timeout=60,
            allow_redirects=True,
        )

        r.raise_for_status()

        return r

    # --------------------------------------------------------

    def post(self, url, data):

        r = self.session.post(
            url,
            data=data,
            timeout=60,
            allow_redirects=True,
        )

        r.raise_for_status()

        return r

    # --------------------------------------------------------

    def login_page(self):

        return self.get(LOGIN_PAGE).text

    # --------------------------------------------------------

    def captcha_url(self, html):

        soup = BeautifulSoup(html, "html.parser")

        img = soup.find(
            "img",
            src=re.compile(r"_CAPTCHA")
        )

        if img is None:
            raise RuntimeError(
                "Couldn't locate CAPTCHA image."
            )

        return urljoin(
            LOGIN_PAGE,
            img["src"]
        )

    # --------------------------------------------------------

    def download_captcha(self, filename):

        html = self.login_page()

        url = self.captcha_url(html)

        r = self.get(url)

        with open(filename, "wb") as f:
            f.write(r.content)

        return filename

    # --------------------------------------------------------

    def login(self, captcha):

        payload = {

            "login_username": USERNAME,

            "secretkey": PASSWORD,

            "captcha": captcha,

            "js_autodetect_results": "1",

            "just_logged_in": "1",

        }

        r = self.post(
            LOGIN_POST,
            payload,
        )


        print("========== LOGIN RESPONSE ==========")
        print(r.url)
        print(r.status_code)
        print(r.text[:5000])
        print("====================================")

        #
        # Save cookies immediately
        #

        self.save_cookies()

        #
        # Verify login
        #

        if "You must be logged in" in r.text:
            return False

        if "incorrect" in r.text.lower():
            return False

        return self.logged_in()

    # --------------------------------------------------------

    def logged_in(self):

        try:
            r = self.get(INBOX_URL)
        except Exception as e:
            print("logged_in() request failed:", e)
            return False

        print("==== logged_in() ====")
        print("URL:", r.url)
        print("Status:", r.status_code)
        print("Cookies:", self.session.cookies.get_dict())
        print(r.text[:500])
        print("=====================")

        if "login.php" in r.url:
            return False

        if "You must be logged in" in r.text:
            return False

        return True


 # --------------------------------------------------------
    # Parse newest message
    # --------------------------------------------------------

    def latest_message(self):

        r = self.get(INBOX_URL)

        if not self.logged_in():
            raise RuntimeError("Not logged in.")

        soup = BeautifulSoup(r.text, "html.parser")

        #
        # Find the first message link.
        #
        # Example:
        # read_body.php?mailbox=INBOX&passed_id=14
        #

        for link in soup.find_all("a", href=True):

            href = link["href"]

            if "read_body.php" not in href:
                continue

            match = re.search(r"passed_id=(\d+)", href)

            if match is None:
                continue

            msg_id = int(match.group(1))

            #
            # Find the table row this link belongs to.
            #

            row = link.find_parent("tr")

            if row is None:
                continue

            cells = row.find_all("td")

            sender = ""
            date = ""
            subject = link.get_text(" ", strip=True)

            #
            # Your inbox layout is:
            #
            # checkbox
            # sender
            # date
            # attachment/icon
            # subject
            #

            if len(cells) >= 5:

                sender = cells[1].get_text(
                    " ",
                    strip=True,
                )

                date = cells[2].get_text(
                    " ",
                    strip=True,
                )

            return MailMessage(
                id=msg_id,
                sender=sender,
                subject=subject,
                date=date,
                url=urljoin(INBOX_URL, href),
            )

        raise RuntimeError(
            "Couldn't locate any messages."
        )

    # --------------------------------------------------------
    # Storage helpers
    # --------------------------------------------------------

    def load_last_id(self, filename="last_message.txt"):

        path = Path(filename)

        if not path.exists():
            return 0

        try:
            return int(path.read_text().strip())
        except Exception:
            return 0

    # --------------------------------------------------------

    def save_last_id(self, msg_id, filename="last_message.txt"):

        Path(filename).write_text(str(msg_id))

    # --------------------------------------------------------
    # Check for new mail
    # --------------------------------------------------------

    def has_new_mail(self):

        last_id = self.load_last_id()

        newest = self.latest_message()

        if newest.id > last_id:

            self.save_last_id(newest.id)

            return True, newest

        return False, newest

    # --------------------------------------------------------
    # Initialize mailbox state
    # --------------------------------------------------------

    def initialize(self):

        newest = self.latest_message()

        self.save_last_id(newest.id)

        return newest

    # --------------------------------------------------------
    # Force refresh
    # --------------------------------------------------------

    def refresh(self):

        return self.has_new_mail()

    # --------------------------------------------------------
    # Connection test
    # --------------------------------------------------------

    def ping(self):

        try:

            r = self.get(LOGIN_PAGE)

            return r.status_code == 200

        except Exception:

            return False
