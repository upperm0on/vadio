import unittest
import json
import socketserver
import threading
from urllib import request
from time import sleep
import os
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from web_app.server import Handler, PORT, RADIO_DIR, VIBE_PATHS

class TestDeliveryAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create dummy data for testing
        cls.vibe_dir = RADIO_DIR / VIBE_PATHS["true warrior"]
        cls.vibe_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dummy mp3s and json metadata
        for i in range(3):
            (cls.vibe_dir / f"test_track_{i}.mp3").touch()
            meta = {"title": f"Test Title {i}", "duration": "100"}
            with open(cls.vibe_dir / f"test_track_{i}.json", "w") as f:
                json.dump(meta, f)

        # Start server in a background thread
        cls.server = socketserver.TCPServer(("", PORT+1), Handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        sleep(1) # wait for server to start

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        # Cleanup dummy files
        for i in range(3):
            (cls.vibe_dir / f"test_track_{i}.mp3").unlink(missing_ok=True)
            (cls.vibe_dir / f"test_track_{i}.json").unlink(missing_ok=True)
        # Try to remove dir if empty
        try:
            cls.vibe_dir.rmdir()
        except OSError:
            pass

    def test_generate_endpoint_metadata(self):
        """TC-4.1 & TC-4.2: Test API returns valid url and metadata"""
        req = request.Request(f"http://localhost:{PORT+1}/generate", method="POST")
        req.add_header('Content-Type', 'application/json')
        data = json.dumps({"vibe": "true warrior"}).encode()
        
        with request.urlopen(req, data=data) as response:
            self.assertEqual(response.status, 200)
            result = json.loads(response.read().decode())
            
            self.assertIn("url", result)
            self.assertTrue(result["url"].endswith(".mp3"))
            self.assertIn("metadata", result)
            self.assertIn("title", result["metadata"])
            self.assertTrue(result["metadata"]["title"].startswith("Test Title"))

if __name__ == "__main__":
    unittest.main()
