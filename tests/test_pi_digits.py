import unittest
from urllib.error import URLError
from urllib.request import Request, urlopen

import mpmath as mp

import generate_pi_bauhaus_poster as poster

REFERENCE_PI_URL = "https://calculat.io/storage/pi/100k.txt"


class TestPiDigits(unittest.TestCase):
    def test_get_pi_digits_matches_reference(self) -> None:
        n = 2000
        mp.mp.dps = n + 20
        expected = str(mp.pi).split('.', 1)[1][:n]
        actual = poster.get_pi_digits(n)
        self.assertEqual(actual, expected)

    def test_feynman_point_sequence(self) -> None:
        n = poster.FEYNMAN_START + poster.FEYNMAN_LEN + 16
        digits = poster.get_pi_digits(n)
        self.assertEqual(digits[poster.FEYNMAN_START:poster.FEYNMAN_START + poster.FEYNMAN_LEN], "999999")

    def test_cells_follow_pi_stream(self) -> None:
        margin_x = poster.WIDTH_PX * poster.MARGIN_RATIO
        margin_y = poster.HEIGHT_PX * poster.MARGIN_RATIO
        inner_w = poster.WIDTH_PX - 2 * margin_x
        inner_h = poster.HEIGHT_PX - 2 * margin_y

        cells = poster.build_cells(margin_x, margin_y, inner_w, inner_h)
        digits = poster.get_pi_digits(len(cells))

        self.assertEqual(len(cells), len(digits))

        sample_indices = [0, 1, 10, 100, poster.FEYNMAN_START, len(cells) - 1]
        for i in sample_indices:
            with self.subTest(index=i):
                self.assertEqual(cells[i].index, i)
                self.assertEqual(cells[i].digit, int(digits[i]))

    def test_get_pi_digits_matches_calculatio_reference(self) -> None:
        n = 5000
        try:
            req = Request(
                REFERENCE_PI_URL,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/plain,*/*;q=0.9",
                    "Accept-Language": "en-US,en;q=0.8",
                    "Referer": "https://calculat.io/en/number/pi/100k/",
                },
            )
            with urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except (URLError, TimeoutError) as exc:
            self.skipTest(f"Network reference unavailable: {exc}")

        all_digits = "".join(ch for ch in raw if ch.isdigit())
        # Source may include leading "3" before decimals.
        if all_digits.startswith("3"):
            all_digits = all_digits[1:]

        self.assertGreaterEqual(len(all_digits), n)
        expected = all_digits[:n]
        actual = poster.get_pi_digits(n)
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
