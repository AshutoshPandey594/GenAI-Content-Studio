import os
import tempfile
import unittest
from unittest.mock import patch

import app as application


class GenAIAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        application.DB_PATH = self.temp_db.name
        application.init_db()
        self.client = application.app.test_client()

    def tearDown(self):
        os.unlink(self.temp_db.name)

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GenAI", response.data)

    def test_empty_prompt_rejected(self):
        response = self.client.post("/api/generate", json={"prompt": "  "})
        self.assertEqual(response.status_code, 400)

    def test_prompt_length_validated(self):
        response = self.client.post("/api/generate", json={"prompt": "x" * 5001})
        self.assertEqual(response.status_code, 400)

    @patch("app.requests.post")
    def test_generate_saves_to_history(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            "response": "A neural network is a model inspired by connected neurons."
        }
        mock_response.raise_for_status.return_value = None

        response = self.client.post("/api/generate", json={
            "prompt": "Explain neural networks",
            "temperature": 0.7,
            "max_tokens": 128
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("output", response.get_json())

        history = self.client.get("/api/history")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.get_json()), 1)

    def test_delete_missing_history_item(self):
        response = self.client.delete("/api/history/999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
