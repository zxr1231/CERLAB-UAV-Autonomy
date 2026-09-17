"""Debounce high-rate Gazebo contacts into collision episodes."""


class CollisionEpisodeAccumulator:
    def __init__(self, quiet_period=0.1):
        self.quiet_period = float(quiet_period)
        self.next_id = 1
        self.active = None
        self.episodes = []
        self.message_count = 0

    def update(self, sim_time, phase, pairs, max_force=0.0, max_depth=0.0):
        sim_time = float(sim_time)
        self.message_count += 1
        completed = self.advance(sim_time)
        pairs = sorted(set(str(pair) for pair in pairs))
        started = False
        if not pairs:
            return completed, started
        if self.active is None:
            self.active = {
                "episode_id": self.next_id,
                "phase": str(phase),
                "start_sim": sim_time,
                "last_contact_sim": sim_time,
                "contact_pairs": set(),
                "max_force_n": 0.0,
                "max_depth_m": 0.0,
            }
            self.next_id += 1
            started = True
        self.active["last_contact_sim"] = sim_time
        self.active["contact_pairs"].update(pairs)
        self.active["max_force_n"] = max(self.active["max_force_n"], float(max_force))
        self.active["max_depth_m"] = max(self.active["max_depth_m"], float(max_depth))
        return completed, started

    def advance(self, sim_time, force=False):
        if self.active is None:
            return []
        sim_time = float(sim_time)
        if not force and sim_time - self.active["last_contact_sim"] < self.quiet_period:
            return []
        episode = dict(self.active)
        episode["end_sim"] = episode.pop("last_contact_sim")
        episode["duration_sim"] = max(0.0, episode["end_sim"] - episode["start_sim"])
        episode["contact_pairs"] = sorted(episode["contact_pairs"])
        self.episodes.append(episode)
        self.active = None
        return [episode]

    def summary(self):
        phases = {}
        for episode in self.episodes:
            phases[episode["phase"]] = phases.get(episode["phase"], 0) + 1
        return {
            "schema_version": 1,
            "status": "VALID" if self.message_count else "NO_CONTACT_MESSAGES",
            "message_count": self.message_count,
            "collision_detected": bool(self.episodes),
            "episode_count": len(self.episodes),
            "episode_count_by_phase": phases,
            "total_contact_duration_sim": sum(
                episode["duration_sim"] for episode in self.episodes),
            "max_force_n": max((episode["max_force_n"] for episode in self.episodes),
                               default=0.0),
            "max_depth_m": max((episode["max_depth_m"] for episode in self.episodes),
                               default=0.0),
        }
