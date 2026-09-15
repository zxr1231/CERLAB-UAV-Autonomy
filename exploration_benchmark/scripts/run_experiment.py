#!/usr/bin/env python3
"""Run one isolated CERLAB simulation benchmark without rosbag."""
import argparse
import datetime
import hashlib
import json
import os
import pty
import re
import selectors
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from exploration_benchmark.core import (atomic_write_json,
                                        create_seed_pair_run_directory,
                                        resolve_seeds)
from exploration_benchmark.trajectory_metrics import write_run_metrics
from exploration_benchmark.resource_metrics import ResourceMonitor


PROMPTS = [
    "Please double check all parameters",
    "Takeoff succeed",
    "PRESS ENTER to Start Planning",
]


def run_output(command, cwd=None):
    return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_path(path, project):
    try:
        return str(path.relative_to(project))
    except ValueError:
        return str(path)


def shell_command(workspace, body):
    return ["/bin/bash", "--noprofile", "--norc", "-c",
            "source /opt/ros/noetic/setup.bash\n"
            "source %s/devel/setup.bash\n%s" % (workspace, body)]


class Process:
    def __init__(self, name, command, log_path, interactive=False, event=None):
        self.name = name
        self.log = Path(log_path).open("ab", buffering=0)
        self.master = None
        self.prompt_stage = 0
        self.event = event
        if interactive:
            self.master, slave = pty.openpty()
            self.process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave,
                                            preexec_fn=os.setsid, close_fds=True)
            os.close(slave)
            self.thread = threading.Thread(target=self._pump, daemon=True)
            self.thread.start()
        else:
            self.process = subprocess.Popen(command, stdout=self.log, stderr=subprocess.STDOUT,
                                            preexec_fn=os.setsid)
        self.pgid = os.getpgid(self.process.pid)

    def _pump(self):
        buffer = ""
        while self.process.poll() is None:
            try:
                chunk = os.read(self.master, 4096)
            except OSError:
                break
            if not chunk:
                break
            self.log.write(chunk)
            buffer = (buffer + chunk.decode("utf-8", errors="replace"))[-4096:]
            if self.prompt_stage < len(PROMPTS) and PROMPTS[self.prompt_stage] in buffer:
                os.write(self.master, b"\n")
                if self.event:
                    self.event("AUTO_CONFIRM", process=self.name,
                               prompt_index=self.prompt_stage + 1)
                self.prompt_stage += 1
                buffer = ""

    def stop(self):
        if self.process.poll() is not None:
            self.log.close()
            return
        os.killpg(self.pgid, signal.SIGINT)
        try:
            self.process.wait(timeout=12)
        except subprocess.TimeoutExpired:
            os.killpg(self.pgid, signal.SIGTERM)
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(self.pgid, signal.SIGKILL)
                self.process.wait(timeout=5)
        self.log.close()


def wait_for_topic(topic, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(["rostopic", "type", topic], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            return True
        time.sleep(0.5)
    return False


def read_ros_clock(timeout=5.0):
    try:
        result = subprocess.run(["rostopic", "echo", "-n", "1", "/clock/clock"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("simulation clock read timeout") from error
    if result.returncode != 0:
        raise RuntimeError("simulation clock read failed: %s" % result.stdout.strip())
    seconds = re.search(r"^secs:\s*(\d+)\s*$", result.stdout, re.MULTILINE)
    nanoseconds = re.search(r"^nsecs:\s*(\d+)\s*$", result.stdout, re.MULTILINE)
    if seconds is None or nanoseconds is None:
        raise RuntimeError("unexpected simulation clock output: %s" % result.stdout.strip())
    return int(seconds.group(1)) + int(nanoseconds.group(1)) * 1e-9


def process_manifest(project, environment_seed, planner_seed, mode,
                     ground_truth_mask=None,
                     ground_truth_metadata=None):
    keys = [
        project / "uav_simulator/launch/start.launch",
        project / "uav_simulator/urdf/quadcopter.urdf",
        project / "autonomous_flight/cfg/dynamic_exploration/flight_base.yaml",
        project / "autonomous_flight/cfg/dynamic_exploration/exploration_param.yaml",
        project / "autonomous_flight/cfg/dynamic_exploration/mapping_param.yaml",
        project / "autonomous_flight/cfg/dynamic_exploration/planner_param.yaml",
    ]
    if ground_truth_mask is not None:
        keys.extend([ground_truth_mask, ground_truth_metadata])
    manifest = {
        "schema_version": 3,
        "status": "RUNNING",
        "method": "hire_return_home_500",
        "mode": mode,
        "seed": environment_seed if environment_seed == planner_seed else None,
        "environment_seed": environment_seed,
        "planner_seed": planner_seed,
        "main_commit": run_output(["git", "rev-parse", "HEAD"], project),
        "branch": run_output(["git", "branch", "--show-current"], project),
        "git_status": run_output(["git", "status", "--porcelain=v1"], project),
        "submodules": run_output(["git", "submodule", "status"], project).splitlines(),
        "files": {manifest_path(path, project): sha256(path) for path in keys},
        "completion_gain_threshold": 500,
        "coverage_status": ("PROVISIONAL_PENDING_RUNTIME_VALIDATION"
                            if ground_truth_mask is not None else
                            "UNAVAILABLE_NO_GROUND_TRUTH_MASK"),
        "record_rosbag": False,
        "start_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": sys.argv,
    }
    if ground_truth_mask is not None:
        metadata = json.loads(ground_truth_metadata.read_text(encoding="utf-8"))
        manifest["ground_truth"] = {
            "mask": str(ground_truth_mask),
            "metadata": str(ground_truth_metadata),
            "mask_content_sha256": metadata["mask_content_sha256"],
            "accessible_denominator": metadata["counts"]["accessible_free"],
            "surface_denominator": metadata["counts"]["static_surface"],
        }
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/home/zxr2/cerlab_benchmark_ws")
    parser.add_argument("--results-root", default="")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--seed", type=int,
                        help="legacy shorthand setting both environment and planner seed")
    parser.add_argument("--environment-seed", type=int)
    parser.add_argument("--planner-seed", type=int)
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--timeout", type=float, default=240.0, help="wall seconds after planning starts")
    parser.add_argument("--rviz", action="store_true")
    parser.add_argument("--ground-truth-mask", default="")
    parser.add_argument("--ground-truth-metadata", default="")
    parser.add_argument("--disable-coverage", action="store_true")
    args = parser.parse_args()
    try:
        environment_seed, planner_seed = resolve_seeds(
            args.seed, args.environment_seed, args.planner_seed)
    except ValueError as error:
        parser.error(str(error))
    workspace = Path(args.workspace).resolve()
    project = workspace / "src/CERLAB-UAV-Autonomy"
    default_mask = project / "experiments/benchmark_v2/masks/floorplan2_static_v1.npz"
    default_metadata = project / "experiments/benchmark_v2/masks/floorplan2_static_v1.metadata.json"
    if args.disable_coverage:
        ground_truth_mask = ground_truth_metadata = None
    else:
        ground_truth_mask = Path(args.ground_truth_mask).resolve() if args.ground_truth_mask else default_mask
        ground_truth_metadata = (Path(args.ground_truth_metadata).resolve()
                                 if args.ground_truth_metadata else default_metadata)
        if not ground_truth_mask.is_file() or not ground_truth_metadata.is_file():
            raise RuntimeError("ground-truth mask/metadata missing; use --disable-coverage explicitly")
    results_root = Path(args.results_root).resolve() if args.results_root else workspace / "results"
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    output = create_seed_pair_run_directory(
        results_root, args.experiment_id, environment_seed, planner_seed, timestamp)
    manifest = process_manifest(project, environment_seed, planner_seed, args.mode,
                                ground_truth_mask, ground_truth_metadata)
    atomic_write_json(output / "run.json", manifest)
    events_stream = (output / "runner_events.jsonl").open("x", encoding="utf-8")
    resource_monitor = ResourceMonitor(output)
    wall_start = time.monotonic()

    def event(event_name, **fields):
        payload = {"event": event_name, "wall_elapsed": time.monotonic()-wall_start}
        payload.update(fields)
        events_stream.write(json.dumps(payload, sort_keys=True) + "\n")
        events_stream.flush()

    processes = []
    outcome = "UNKNOWN"
    error = None
    resource_started = False
    resource_groups = {}
    try:
        if subprocess.run(["rosnode", "list"], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0:
            raise RuntimeError("ROS Master already exists; refuse duplicate benchmark")
        simulator_body = ("source %s/uav_simulator/gazeboSetup.bash\n"
                          "exec roslaunch uav_simulator start.launch gazebo_seed:=%d gui:=%s" %
                          (project, environment_seed, "true" if args.rviz else "false"))
        simulator = Process("simulator", shell_command(workspace, simulator_body),
                            output / "simulator.log", event=event)
        processes.append(simulator)
        event("PROCESS_STARTED", name="simulator", pid=simulator.process.pid)
        if not wait_for_topic("/CERLAB/quadcopter/odom", 60):
            raise RuntimeError("odometry topic timeout")
        if not wait_for_topic("/camera/depth/image_raw", 60):
            raise RuntimeError("depth topic timeout")
        if not wait_for_topic("/CERLAB/quadcopter/contacts", 30):
            raise RuntimeError("quadcopter contact topic timeout")
        manifest["collision_measurement_status"] = "CONTACT_TOPIC_VERIFIED"
        logger_body = ("exec roslaunch exploration_benchmark logger.launch output_dir:=%s "
                       "ground_truth_mask:=%s ground_truth_metadata:=%s" %
                       (shlex.quote(str(output)),
                        shlex.quote(str(ground_truth_mask)) if ground_truth_mask else "''",
                        shlex.quote(str(ground_truth_metadata)) if ground_truth_metadata else "''"))
        logger = Process("logger", shell_command(workspace, logger_body),
                         output / "logger.log", event=event)
        processes.append(logger)
        event("PROCESS_STARTED", name="logger", pid=logger.process.pid)
        if args.rviz:
            rviz = Process("rviz", shell_command(workspace,
                "exec roslaunch remote_control exploration_rviz.launch"),
                output / "rviz.log", event=event)
            processes.append(rviz)
            event("PROCESS_STARTED", name="rviz", pid=rviz.process.pid)
        launch = "return_home_smoke.launch" if args.mode == "smoke" else "dynamic_exploration.launch"
        exploration_body = ("exec roslaunch autonomous_flight %s benchmark_seed:=%d" %
                            (launch, planner_seed))
        exploration = Process("exploration", shell_command(workspace, exploration_body),
                              output / "exploration.log", interactive=True, event=event)
        processes.append(exploration)
        event("PROCESS_STARTED", name="exploration", pid=exploration.process.pid)
        prompt_deadline = time.monotonic() + 90
        while exploration.prompt_stage < 3 and time.monotonic() < prompt_deadline:
            if exploration.process.poll() is not None:
                raise RuntimeError("exploration exited during confirmations")
            time.sleep(0.2)
        if exploration.prompt_stage < 3:
            raise RuntimeError("official confirmation prompt timeout")
        try:
            planning_start_sim = read_ros_clock()
        except RuntimeError:
            if ground_truth_mask is not None:
                raise
            planning_start_sim = None
        planning_start = {
            "schema_version": 1,
            "event": "PLANNING_ACTIVE",
            "sim_time": planning_start_sim,
            "wall_elapsed": time.monotonic()-wall_start,
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        atomic_write_json(output / "planning_start.json", planning_start)
        manifest["planning_start_sim"] = planning_start_sim
        event("EXPLORATION_STARTED", sim_time=planning_start_sim)
        subprocess.run(["rosparam", "dump", str(output / "rosparams.yaml")], check=True)
        resource_groups = {process.name: process.process.pid for process in processes}
        resource_monitor.sample(time.monotonic()-wall_start, planning_start_sim,
                                resource_groups)
        resource_started = True
        next_resource_sample = time.monotonic() + 1.0
        deadline = time.monotonic() + args.timeout
        home_since = None
        latest_sim_time = planning_start_sim
        while time.monotonic() < deadline:
            for process in processes:
                if process.process.poll() is not None:
                    raise RuntimeError("%s exited with code %s" %
                                       (process.name, process.process.returncode))
            status_path = output / "live_status.json"
            if status_path.exists():
                try:
                    status = json.loads(status_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    status = {}
                latest_sim_time = status.get("sim_time", latest_sim_time)
                if status.get("mission_state") == "HOME_REACHED":
                    if home_since is None:
                        home_since = time.monotonic()
                        event("HOME_REACHED_MONITOR")
                    if time.monotonic() - home_since >= 10:
                        outcome = "HOME_REACHED"
                        break
                else:
                    home_since = None
            if time.monotonic() >= next_resource_sample:
                resource_monitor.sample(time.monotonic()-wall_start, latest_sim_time,
                                        resource_groups)
                next_resource_sample += 1.0
            time.sleep(0.5)
        else:
            outcome = "TIMEOUT"
    except KeyboardInterrupt:
        outcome = "USER_ABORT"
    except Exception as exception:
        outcome = "PROCESS_ERROR"
        error = str(exception)
        event("RUNNER_ERROR", error=error)
    finally:
        event("RUNNER_STOPPING", outcome=outcome)
        for process in reversed(processes):
            try:
                process.stop()
            except Exception as stop_error:
                event("STOP_ERROR", process=process.name, error=str(stop_error))
        try:
            resource_summary = resource_monitor.close()
            manifest["resource_metrics_status"] = resource_summary["status"]
        except Exception as resource_error:
            manifest["resource_metrics_status"] = "INVALID"
            event("RESOURCE_METRICS_ERROR", error=str(resource_error),
                  sampling_started=resource_started)
        try:
            trajectory_metrics = write_run_metrics(output)
            manifest["trajectory_metrics_status"] = trajectory_metrics["status"]
        except Exception as metrics_error:
            manifest["trajectory_metrics_status"] = "INVALID"
            event("TRAJECTORY_METRICS_ERROR", error=str(metrics_error))
        events_stream.close()
        summary_path = output / "summary.json"
        if summary_path.exists():
            try:
                final_summary = json.loads(summary_path.read_text(encoding="utf-8"))
                manifest["coverage_status"] = final_summary.get(
                    "coverage_status", manifest["coverage_status"])
                manifest["collision_measurement_status"] = final_summary.get(
                    "collision", {}).get("status", "INVALID_COLLISION_SUMMARY")
            except (OSError, ValueError):
                manifest["coverage_status"] = "INVALID_SUMMARY_JSON"
        manifest.update({
            "status": "VERIFIED" if outcome == "HOME_REACHED" else "FAILED",
            "measurement_status": manifest["coverage_status"],
            "outcome": outcome,
            "error": error,
            "end_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "wall_duration": time.monotonic()-wall_start,
        })
        atomic_write_json(output / "run.json", manifest)
        atomic_write_json(output / "runner_result.json", {
            "outcome": outcome, "error": error,
            "wall_duration": time.monotonic()-wall_start,
        })
        print(str(output))
    return 0 if outcome == "HOME_REACHED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
