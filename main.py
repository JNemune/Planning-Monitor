import datetime
from json import dump, load
from os.path import join
from pprint import pformat

import arabic_reshaper
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from pyrogram import Client, filters
from pyrogram.types.messages_and_media.message import Message


class App(object):
    def __init__(self) -> None:
        with open(join(".", "target", "config.json"), "r", encoding="utf-8") as f:
            config = load(f)
            api_id = config["api_id"]
            api_hash = config["api_hash"]
            bot_token = config["bot_token"]

        self.app = Client(
            "Planning-Monitor", api_id=api_id, api_hash=api_hash, bot_token=bot_token
        )
        self.CA_IR_delta = datetime.timedelta(hours=8, minutes=30)

        self.telegram_manager()
        self.app.run()

    def data_reader(self, id, case) -> dict:
        """
        read tasks.json and done.json and return dict of it
        """
        with open(join(".", "data", id, f"{case}.json"), "r", encoding="utf-8") as f:
            out = load(f)
        return out

    def plot(self, id) -> None:
        """
        plot percentage of time used and save the fig
        """

        def persian_text(inp: str):
            return get_display(arabic_reshaper.reshape(inp))

        done = self.data_reader(id, "done")
        tasks = self.data_reader(id, "tasks")
        fig, ax = plt.subplots()
        bar_colors = [
            "tab:blue",
            "tab:orange",
            "tab:green",
            "tab:red",
            "tab:purple",
            "tab:brown",
            "tab:pink",
            "tab:gray",
            "tab:olive",
            "tab:cyan",
        ]

        c = 0
        for i_, i in enumerate(tasks):
            for j_, j in enumerate(tasks[i]):
                c += 1
                ax.bar(
                    persian_text(j),
                    100
                    * (
                        sum(k["time"] for k in done[i][j])
                        if i in done and j in done[i]
                        else 0
                    )
                    / tasks[i][j]
                    / 3600,
                    label=persian_text(i) if j_ == 0 else "_" + persian_text(i),
                    color=bar_colors[i_],
                )
        ax.hlines(
            (
                datetime.datetime.now()
                - datetime.datetime.fromisoformat(done["main_time"])
            ).total_seconds()
            / 6048,
            -0.3,
            c - 0.7,
            color="black",
        )

        ax.set_ylabel("Percentage of Time Used (%)")
        ax.set_title("Planning Monitor")
        ax.legend(title="Categories")

        fig.savefig(join(".", "data", id, "plot.png"))

    def do(self, id, category: str = "", task: str = "", detail: str = "") -> bool:
        """
        done tasks commit on data/done.json
        """
        done = self.data_reader(id, "done")
        tasks = self.data_reader(id, "tasks")

        if category not in tasks or task not in tasks[category]:
            return False

        time = datetime.datetime.now() + self.CA_IR_delta

        done[category] = done.get(category, {})
        done[category][task] = done[category].get(task, []) + [
            {
                "detail": detail,
                "start_time": done["start_time"],
                "end_time": time.isoformat(),
                "time": (
                    time - datetime.datetime.fromisoformat(done["start_time"])
                ).total_seconds(),
            }
        ]
        done["start_time"] = time.isoformat()

        with open(join(".", "data", id, "done.json"), "w", encoding="utf-8") as f:
            dump(done, f, ensure_ascii=False)

        return True

    def telegram_manager(self) -> None:
        @self.app.on_message(filters.text & filters.private)
        async def new_message(client: Client, m: Message):
            match m.text:
                case "plot":
                    self.plot(str(m.chat.id))
                    await m.reply_photo(join(".", "data", str(m.chat.id), "plot.png"))
                case "tasks" | "done":
                    await m.reply(
                        "__" + pformat(self.data_reader(str(m.chat.id), m.text)) + "__"
                    )
                case _:
                    msg = m.text.split("\n")
                    if self.do(str(m.chat.id), *msg):
                        await m.reply("ثبت شد ✅")
                    else:
                        await m.reply("ثبت نشد ❌")


if __name__ == "__main__":
    app = App()
