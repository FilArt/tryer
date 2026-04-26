import json
from openai import OpenAI


class Planner:
    def __init__(
        self, model: str, movies_dir: str, series_dir: str, api_key: str = "local", base_url: str | None = None
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model or self.default_model()
        self.movies_dir = movies_dir
        self.series_dir = series_dir

    def default_model(self) -> str:
        models = self.client.models.list()
        return models.data[0].id

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

    def ask_stream(self, prompt: str):
        stream = self.client.chat.completions.create(
            model=self.model,
            stream=True,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the assistant inside a Telegram media organizer bot. "
                        "The bot accepts magnet links and .torrent files, sends downloads to qBittorrent, "
                        "organizes completed video files for Jellyfin, and can answer user questions here. "
                        "You run through an OpenAI-compatible chat API and cannot directly use Telegram, "
                        "run shell commands, access files, change settings, or move media by yourself. "
                        "When the user asks for actions, explain what the bot can do or what command/input "
                        "they should send. Answer briefly and directly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
