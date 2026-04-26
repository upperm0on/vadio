import unittest
import os
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

class TestDiscovery(unittest.TestCase):
    def test_vibe_classification(self):
        """TC-1.2: Ensure keywords are correctly classified into vibes."""
        from reddit_matrix import classify_title
        
        self.assertEqual(classify_title("Godly Sukuna Aura Edit"), "Cinematic Aura")
        self.assertEqual(classify_title("Love Me Breakdown Agony"), "Mental Agony")
        self.assertEqual(classify_title("Stoic Thorfinn True Warrior peace"), "True Warrior")
        
    def test_query_normalization(self):
        """TC-1.1: Ensure queries are cleaned and normalized."""
        from reddit_matrix import seed_query_from_title
        
        title = "  AMAZING!! Sukuna [4K] Edit  "
        query = seed_query_from_title(title)
        self.assertIn("sukuna", query)
        self.assertNotIn("!!", query)
        self.assertNotIn("[4K]", query)

if __name__ == "__main__":
    unittest.main()
