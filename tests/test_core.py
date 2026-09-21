import os
import sys
import unittest
import asyncio

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import crypto_patch
import database
from network_utils import format_size, format_duration, make_safe_filename
from server import create_app, RANGE_REGEX, PLAYER_TEMPLATE_PATH

class MockClient:
    async def get_messages(self, chat_id, message_id):
        return None

class MockBotMe:
    username = "TestBot"
    first_name = "Test Streamer"

class TestCoreModules(unittest.TestCase):
    def test_network_utils(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1048576), "1.00 MB")
        self.assertEqual(format_size(1073741824), "1.00 GB")

        self.assertEqual(format_duration(0), "00:00")
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3665), "01:01:05")

        self.assertEqual(make_safe_filename("Tokyo/Ghoul:143.mp4"), "TokyoGhoul143.mp4")
        self.assertEqual(make_safe_filename("../test.mkv"), "..test.mkv")

    def test_range_regex(self):
        m1 = RANGE_REGEX.match("bytes=0-1048575")
        self.assertIsNotNone(m1)
        self.assertEqual(m1.groups(), ("0", "1048575"))

        m2 = RANGE_REGEX.match("bytes=500-")
        self.assertIsNotNone(m2)
        self.assertEqual(m2.groups(), ("500", ""))

    def test_database_async(self):
        async def run_db_test():
            await database.init_db()
            test_id = "test_link_123"
            await database.save_media(
                link_id=test_id,
                chat_id=12345,
                message_id=67890,
                file_id="tg_file_abc",
                file_name="Anime_Episode_01.mp4",
                file_size=524288000,
                mime_type="video/mp4",
                duration=1440
            )

            record = await database.get_media(test_id)
            self.assertIsNotNone(record)
            self.assertEqual(record["file_name"], "Anime_Episode_01.mp4")
            self.assertEqual(record["file_size"], 524288000)
            self.assertEqual(record["duration"], 1440)

        asyncio.run(run_db_test())

    def test_server_routes_registered(self):
        client = MockClient()
        bot_me = MockBotMe()
        app = create_app(client, bot_me, 8080)
        routes = [r.resource.canonical for r in app.router.routes()]
        self.assertIn("/", routes)
        self.assertIn("/status", routes)
        self.assertIn("/play/{link_id}", routes)
        self.assertIn("/stream/{link_id}", routes)
        self.assertIn("/dl/{link_id}", routes)

    def test_player_template_render(self):
        self.assertTrue(os.path.exists(PLAYER_TEMPLATE_PATH))
        with open(PLAYER_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("کاویمو", content)
        self.assertIn("data-speed=\"2.5\"", content)
        self.assertIn("double-tap-zone", content)
        self.assertIn("Vazirmatn", content)

if __name__ == "__main__":
    unittest.main()
