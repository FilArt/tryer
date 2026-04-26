import json
from openai import OpenAI


class Planner:
    def __init__(self, model: str, movies_dir: str, series_dir: str):
        self.client = OpenAI()
        self.model = model
        self.movies_dir = movies_dir
        self.series_dir = series_dir

    def plan(self, torrent_name: str, files: list[str]) -> dict:
        prompt = {
            "torrent_name": torrent_name,
            "files": files,
            "movies_dir": self.movies_dir,
            "series_dir": self.series_dir,
            "rules": {
                "movie": "movies_dir/Movie Name (Year)/Movie Name (Year).ext",
                "series": "series_dir/Series Name/Season 01/Series Name - S01E01.ext",
            },
        }
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return only JSON with content_type, title, year, confidence, items, ignored_files. Each item must have source and target.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")
