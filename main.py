import datetime
from json import dump, load
from os.path import join


class App(object):
    def __init__(self) -> None:
        self.CA_IR_delta = datetime.timedelta(hours=8, minutes=30)

    def tasks_print(self) -> None:
        pass

    def done_print(self) -> None:
        pass

    def plot(self) -> None:
        pass

    def do(self, group: str, task: str, detail: str) -> bool:
        """
        done tasks commit on target/done.json
        """
        with open(join(".", "target", "done.json"), "r", encoding="utf-8") as f:
            done = load(f)
        with open(join(".", "target", "tasks.json"), "r", encoding="utf-8") as f:
            tasks = load(f)
        if group not in tasks or task not in tasks[group]:
            return False
        time = datetime.datetime.now() + self.CA_IR_delta

        done[group] = done.get(group, {})
        done[group][task] = done[group].get(task, []) + [
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

        with open(join(".", "target", "done.json"), "r", encoding="utf-8") as f:
            dump(done, f, ensure_ascii=False)

    def telegram_manager(self) -> None:
        pass


print(datetime.datetime.now() + datetime.timedelta(hours=8, minutes=30))
