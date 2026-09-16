"""A minimal, faithful reimplementation of the event-driven engine, used only to
produce the numbers behind the figures on this page.

It follows the documented semantics of the prototype: an event queue holding
arrivals and completions, a virtual clock that jumps to the next event, a system
state updated after every event, arrival/completion handlers, and a pluggable
scheduling policy. Nothing here executes real work; it moves metadata rows
through a simulated cluster.
"""
from __future__ import annotations

import heapq
import random
from dataclasses import dataclass, field


@dataclass
class Task:
    task_id: str
    arrival: float
    runtime: float
    cpu: int
    gpu: int
    mem: float
    priority: int
    status: str = "waiting"
    start: float | None = None
    finish: float | None = None

    @property
    def wait(self) -> float | None:
        return None if self.start is None else self.start - self.arrival

    @property
    def turnaround(self) -> float | None:
        return None if self.finish is None else self.finish - self.arrival


@dataclass
class Cluster:
    cpus: int
    gpus: int
    mem: float


@dataclass
class Result:
    tasks: list[Task]
    timeline: list[tuple]          # (t, waiting, running, completed, rejected)
    utilization: list[tuple]       # (t, cpu_used, gpu_used, mem_used)
    events: list[tuple]            # (t, kind, task_id)
    policy: str
    cluster: Cluster = field(default=None)

    @property
    def completed(self) -> list[Task]:
        return [t for t in self.tasks if t.status == "completed"]

    @property
    def rejected(self) -> list[Task]:
        return [t for t in self.tasks if t.status == "rejected"]

    @property
    def makespan(self) -> float:
        return max((t.finish for t in self.completed), default=0.0)

    @property
    def mean_wait(self) -> float:
        w = [t.wait for t in self.completed]
        return sum(w) / len(w) if w else 0.0

    @property
    def mean_turnaround(self) -> float:
        v = [t.turnaround for t in self.completed]
        return sum(v) / len(v) if v else 0.0


# --------------------------------------------------------------- policies
def order_waiting(waiting: list[Task], policy: str, rng: random.Random) -> list[Task]:
    """Return the waiting queue in the order this policy wants it considered."""
    if policy == "FCFS":
        return sorted(waiting, key=lambda t: (t.arrival, t.task_id))
    if policy == "SJF":
        return sorted(waiting, key=lambda t: (t.runtime, t.arrival, t.task_id))
    if policy == "Priority":
        return sorted(waiting, key=lambda t: (t.priority, t.arrival, t.task_id))
    if policy == "Random":
        shuffled = list(waiting)
        rng.shuffle(shuffled)
        return shuffled
    raise ValueError(f"unknown policy: {policy}")


def simulate(tasks: list[Task], cluster: Cluster, policy: str = "FCFS",
             seed: int = 7) -> Result:
    rng = random.Random(seed)
    tasks = [Task(**{k: v for k, v in vars(t).items()
                     if k in {"task_id", "arrival", "runtime", "cpu", "gpu",
                              "mem", "priority"}}) for t in tasks]
    by_id = {t.task_id: t for t in tasks}

    free_cpu, free_gpu, free_mem = cluster.cpus, cluster.gpus, cluster.mem
    waiting: list[Task] = []
    running: set[str] = set()
    completed = rejected = 0

    queue: list[tuple] = []
    seq = 0
    for t in tasks:                       # one arrival event per task
        heapq.heappush(queue, (t.arrival, seq, "arrival", t.task_id))
        seq += 1

    timeline: list[tuple] = []
    utilization: list[tuple] = []
    events: list[tuple] = []
    clock = 0.0

    def record():
        timeline.append((clock, len(waiting), len(running), completed, rejected))
        utilization.append((clock, cluster.cpus - free_cpu,
                            cluster.gpus - free_gpu, cluster.mem - free_mem))

    def try_schedule():
        """Consider waiting tasks in policy order and start every one that fits.

        A task the policy ranks first but that cannot fit right now does not
        block the queue: the engine keeps looking, so small or CPU-only work can
        proceed while a large GPU task waits for capacity.
        """
        nonlocal free_cpu, free_gpu, free_mem, seq
        started = True
        while started:
            started = False
            for task in order_waiting(waiting, policy, rng):
                if (task.cpu <= free_cpu and task.gpu <= free_gpu
                        and task.mem <= free_mem):
                    free_cpu -= task.cpu
                    free_gpu -= task.gpu
                    free_mem -= task.mem
                    task.status = "running"
                    task.start = clock
                    task.finish = clock + task.runtime
                    waiting.remove(task)
                    running.add(task.task_id)
                    heapq.heappush(queue, (task.finish, seq, "completion", task.task_id))
                    seq += 1
                    events.append((clock, "start", task.task_id))
                    started = True
                    break

    while queue:
        clock, _, kind, task_id = heapq.heappop(queue)
        task = by_id[task_id]

        if kind == "arrival":
            events.append((clock, "arrival", task_id))
            # A task that can never fit the whole cluster is rejected, not queued
            # forever; it is reported so the mismatch is visible.
            if (task.cpu > cluster.cpus or task.gpu > cluster.gpus
                    or task.mem > cluster.mem):
                task.status = "rejected"
                rejected += 1
            else:
                waiting.append(task)
                try_schedule()
        else:
            free_cpu += task.cpu
            free_gpu += task.gpu
            free_mem += task.mem
            task.status = "completed"
            running.discard(task_id)
            completed += 1
            events.append((clock, "completion", task_id))
            try_schedule()

        record()

    return Result(tasks, timeline, utilization, events, policy, cluster)


# ------------------------------------------------- the workload in the figures
CLUSTER = Cluster(cpus=16, gpus=2, mem=256)

WORKLOAD = [
    #      id  arrival runtime cpu gpu  mem  prio
    Task("T01",     0,    900,  12,  0,   64, 3),
    Task("T02",     0,    240,   8,  1,   48, 2),
    Task("T03",    30,    120,   4,  0,   32, 4),
    Task("T04",    60,    150,   4,  0,   24, 4),
    Task("T05",    90,    600,  10,  1,   96, 2),
    Task("T06",   120,     90,   2,  0,   16, 5),
    Task("T07",   150,    420,   8,  0,   64, 3),
    Task("T08",   200,     60,   2,  0,   12, 5),
    Task("T09",   240,    330,   6,  1,   40, 3),
    Task("T10",   300,    120,   4,  0,   28, 4),
    Task("T11",   360,    720,  14,  0,  128, 1),
    Task("T12",   420,     75,   3,  0,   20, 5),
    Task("T13",   480,    300,  24,  0,   64, 3),   # 24 CPUs on a 16-CPU cluster
]


if __name__ == "__main__":
    for policy in ("FCFS", "SJF", "Priority", "Random"):
        r = simulate(WORKLOAD, CLUSTER, policy)
        print(f"{policy:9s} makespan={r.makespan:7.0f}s  "
              f"mean wait={r.mean_wait:7.1f}s  "
              f"mean turnaround={r.mean_turnaround:7.1f}s  "
              f"completed={len(r.completed):2d}  rejected={len(r.rejected)}  "
              f"events={len(r.events)}")
