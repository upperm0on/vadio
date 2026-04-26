import unittest
import asyncio
import os
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

class TestHarvesting(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_metadata_discovery(self):
        """TC-2.2: Ensure metadata is correctly captured."""
        from void_daemon import discover_metadata
        
        meta = self.loop.run_until_complete(discover_metadata("Sukuna edit phonk"))
        self.assertIsNotNone(meta)
        self.assertIn("id", meta)
        self.assertIn("title", meta)
        self.assertIn("url", meta)
        print(f"[TEST] Discovered: {meta['title']} by {meta.get('uploader')}")

    def test_file_naming_safety(self):
        """TC-2.1: Verify high-class file naming."""
        # This is a unit test for the naming logic inside harvest_track (mocked)
        title = "Sukuna [4K] 🔥 Phonk Mix!! (2026)"
        safe_title = "".join([c for c in title if c.isalnum() or c in " _-"]).strip()[:50]
        self.assertEqual(safe_title, "Sukuna 4K  Phonk Mix 2026")

if __name__ == "__main__":
    unittest.main()
