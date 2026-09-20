class Benchmark:

    def __init__(self):
        self.results = {}

    def add_job_result(self, job_id, metrics):
        self.results[job_id] = metrics

    def get_total_wait_time(self):
        return sum(
            metrics["wait_time"]
            for metrics in self.results.values()
        )

    def get_average_wait_time(self):
        if not self.results:
            return 0.0

        return self.get_total_wait_time() / len(self.results)

    def get_makespan(self):
        if not self.results:
            return 0.0

        start_times = [
            metrics["submit_time"]
            for metrics in self.results.values()
        ]

        end_times = [
            metrics["end_time"]
            for metrics in self.results.values()
        ]

        return max(end_times) - min(start_times)

    def get_throughput(self):
        makespan = self.get_makespan()

        if makespan <= 0:
            return 0.0

        return len(self.results) / makespan

    def print_summary(self):
        print("\n========== BENCHMARK SUMMARY ==========")

        print(
            f"Total wait time: "
            f"{self.get_total_wait_time():.2f} seconds"
        )

        print(
            f"Average wait time: "
            f"{self.get_average_wait_time():.2f} seconds"
        )

        print(
            f"Makespan: "
            f"{self.get_makespan():.2f} seconds"
        )

        print(
            f"Throughput: "
            f"{self.get_throughput():.4f} jobs/second"
        )

        print("\nPer-job results:")

        for job_id, metrics in self.results.items():
            print(
                f"{job_id}: "
                f"wait={metrics['wait_time']:.2f}s, "
                f"runtime={metrics['runtime']:.2f}s"
            )

        print("=======================================\n")