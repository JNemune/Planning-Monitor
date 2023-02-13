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
            self.admin = config["admin"]

        self.app = Client(
            "Planning-Monitor", api_id=api_id, api_hash=api_hash, bot_token=bot_token
        )
        self.CA_IR_delta = datetime.timedelta(hours=8, minutes=30)

        self.telegram_manager()
        self.app.run()

    def data_reader(self, case) -> dict:
        """
        read tasks.json and done.json and return dict of it
        """
        with open(join(".", "target", f"{case}.json"), "r", encoding="utf-8") as f:
            out = load(f)
        return out

    def plot(self) -> None:
        """
        plot percentage of time used and save the fig
        """

        def persian_text(inp: str):
            return get_display(arabic_reshaper.reshape(inp))

        done = self.data_reader("done")
        tasks = self.data_reader("tasks")
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

        for i_, i in enumerate(tasks):
            for j_, j in enumerate(tasks[i]):
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

        ax.set_ylabel("Percentage of Time Used (%)")
        ax.set_title("Planning Monitor")
        ax.legend(title="Categories")

        fig.savefig(join(".", "target", "plot.png"))

    def do(self, category: str, task: str, detail: str) -> bool:
        """
        done tasks commit on target/done.json
        """
        done = self.data_reader("done")
        tasks = self.data_reader("tasks")

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

        with open(join(".", "target", "done.json"), "w", encoding="utf-8") as f:
            dump(done, f, ensure_ascii=False)

        return True

    def telegram_manager(self) -> None:
        @self.app.on_message(filters.chat(int(self.admin)))
        async def new_message(client: Client, m: Message):
            match m.text:
                case "plot":
                    await m.reply_photo("__" + join(".", "target", "plot.png") + "__")
                case "tasks" | "done":
                    await m.reply(pformat(self.data_reader(m.text)))
                case _:
                    msg = m.text.split("\n")
                    if self.do(*msg):
                        await m.reply("ثبت شد ✅")
                    else:
                        await m.reply("ثبت نشد ❌")


if __name__ == "__main__":
    app = App()
