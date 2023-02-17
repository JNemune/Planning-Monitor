from datetime import datetime as dt
from datetime import timedelta
from json import dump, load
from os import makedirs, remove
from os.path import exists, join

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
        self.CA_IR_delta = timedelta(hours=8, minutes=30)

        self.telegram_manager()
        self.app.run()

    def data_reader(self, id, case) -> dict:
        """
        read tasks.json and done.json and return dict of it
        """
        match case:
            case "done":
                with open(
                    join(".", "data", id, "done.json"), "r", encoding="utf-8"
                ) as f:
                    out = load(f)
                return out
            case "tasks" | "start_time":
                with open(
                    join(".", "data", id, "tasks.json"), "r", encoding="utf-8"
                ) as f:
                    out = load(f)
                return out["tasks"] if case == "tasks" else out["start_time"]

    def plot(self, id) -> None:
        """
        plot percentage of time used and save the fig
        """

        def persian_text(inp: str):
            return get_display(arabic_reshaper.reshape(inp))

        done = self.data_reader(id, "done")
        tasks = self.data_reader(id, "tasks")
        start_time = dt.fromisoformat(self.data_reader(id, "start_time"))
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
                        sum(
                            k["time"]
                            if dt.fromisoformat(k["start_time"]) >= start_time
                            else (
                                dt.fromisoformat(k["end_time"]) - start_time
                            ).total_seconds()
                            if dt.fromisoformat(k["end_time"]) >= start_time
                            else 0
                            for k in done[i][j]
                        )
                        if i in done and j in done[i]
                        else 0
                    )
                    / tasks[i][j]
                    / 3600,
                    label=persian_text(i) if j_ == 0 else "_" + persian_text(i),
                    color=bar_colors[i_],
                )
        ax.hlines(
            (dt.now() + self.CA_IR_delta - start_time).total_seconds()
            / sum([tasks[i][j] for i in tasks for j in tasks[i]])
            / 36,
            -0.4,
            c - 0.6,
            color="black",
        )

        ax.set_ylabel("Percentage of Time Used (%)")
        ax.set_title("Planning Monitor")
        ax.legend(title="Categories")

        fig.set_size_inches(18.5, 10.5)
        fig.savefig(join(".", "data", id, "plot.png"))

    def do(self, id, category: str = "", task: str = "", detail: str = "") -> bool:
        """
        done tasks commit on data/done.json
        """
        done = self.data_reader(id, "done")
        tasks = self.data_reader(id, "tasks")

        if category not in tasks or task not in tasks[category]:
            return False

        time = dt.now() + self.CA_IR_delta

        done[category] = done.get(category, {})
        done[category][task] = done[category].get(task, []) + [
            {
                "detail": detail,
                "start_time": done["start_time"],
                "end_time": time.isoformat(),
                "time": (time - dt.fromisoformat(done["start_time"])).total_seconds(),
            }
        ]
        done["start_time"] = time.isoformat()

        with open(join(".", "data", id, "done.json"), "w", encoding="utf-8") as f:
            dump(done, f, ensure_ascii=False)

        return True

    def telegram_manager(self) -> None:
        @self.app.on_message(filters.text & filters.private)
        async def new_message(client: Client, m: Message):
            if not exists(join(".", "data", str(m.chat.id))):
                makedirs(join(".", "data", str(m.chat.id)))
                with open(join(".", "data", str(m.chat.id), "done.json"), "w") as f:
                    dump(
                        {"start_time": (dt.now() + self.CA_IR_delta).isoformat()},
                        f,
                        ensure_ascii=False,
                    )
                return

            if not exists(join(".", "data", str(m.chat.id), "tasks.json")):
                await m.reply("No tasks set.")
                return

            match m.text:
                case "plot":
                    self.plot(str(m.chat.id))
                    await m.reply_photo(join(".", "data", str(m.chat.id), "plot.png"))
                case "tasks" | "done":
                    await m.reply_document(
                        join(".", "data", str(m.chat.id), m.text + ".json")
                    )
                case _:
                    msg = m.text.split("\n")
                    if self.do(str(m.chat.id), *msg):
                        await m.reply("ثبت شد ✅")
                    else:
                        await m.reply("ثبت نشد ❌")

        @self.app.on_message(filters.document & filters.private)
        async def new_file(client: Client, m: Message):
            await m.download(join(".", "data", str(m.chat.id), "tasks.json"))
            try:
                self.data_reader(str(m.chat.id), "start_time")
                tasks = self.data_reader(str(m.chat.id), "tasks")
                await m.reply(str(sum([tasks[i][j] for i in tasks for j in tasks[i]])))
            except:
                remove(join(".", "data", str(m.chat.id), "tasks.json"))


if __name__ == "__main__":
    app = App()
