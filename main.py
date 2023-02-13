import datetime
from json import dump, load
from os.path import join

import arabic_reshaper
import matplotlib.pyplot as plt
from bidi.algorithm import get_display


class App(object):
    def __init__(self) -> None:
        self.CA_IR_delta = datetime.timedelta(hours=8, minutes=30)

    def tasks_print(self) -> None:
        pass

    def done_print(self) -> None:
        pass

    def plot(self) -> None:
        """
        plot percentage of time used and save the fig
        """

        def persian_text(inp: str):
            return get_display(arabic_reshaper.reshape(inp))

        with open(join(".", "target", "done.json"), "r", encoding="utf-8") as f:
            done = load(f)
        with open(join(".", "target", "tasks.json"), "r", encoding="utf-8") as f:
            tasks = load(f)
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
        with open(join(".", "target", "done.json"), "r", encoding="utf-8") as f:
            done = load(f)
        with open(join(".", "target", "tasks.json"), "r", encoding="utf-8") as f:
            tasks = load(f)
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

    def telegram_manager(self) -> None:
        pass


if __name__ == "__main__":
    app = App()
    app.do("متفرقه", "خواب", "درس")
    app.plot()
