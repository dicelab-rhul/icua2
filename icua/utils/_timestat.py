"""DEPRECATED."""

import time


__all__ = ("TimeStat",)


class TimeStat:
    def __init__(self):
        self.reset_stats()

    def reset_stats(self):
        self.count = 0
        self.total_time = 0
        self.min_time = float("inf")
        self.max_time = float("-inf")
        self.avg_time = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.count += 1
        self.total_time += elapsed_time

        # Update min and max times
        self.min_time = min(self.min_time, elapsed_time)
        self.max_time = max(self.max_time, elapsed_time)

        # Update the average time
        if self.count > 0:
            self.avg_time = self.total_time / self.count

    def get_stat(self):
        stats = {
            "min_time": self.min_time if self.count > 0 else None,
            "max_time": self.max_time if self.count > 0 else None,
            "avg_time": self.avg_time if self.count > 0 else None,
        }
        # Reset the stats after returning them
        self.reset_stats()
        return stats


if __name__ == "__main__":
    # Example usage
    with TimeStat() as timer:
        # Code block whose execution time you want to measure
        time.sleep(1)

    stats = timer.get_stat()
    print(stats)
