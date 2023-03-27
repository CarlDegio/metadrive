import pickle
import numpy as np

from metadrive import MultiAgentRoundaboutEnv
from metadrive.component.map.base_map import BaseMap
from metadrive.component.map.pg_map import MapGenerateMethod
from metadrive.envs.safe_metadrive_env import SafeMetaDriveEnv
from metadrive.manager.traffic_manager import TrafficMode
from metadrive.policy.idm_policy import IDMPolicy
from metadrive.utils import setup_logger


def test_save_episode(vis=False):
    setup_logger(True)

    test_dump = True
    save_episode = True
    vis = vis
    env = SafeMetaDriveEnv(
        {
            "accident_prob": 0.8,
            "environment_num": 1,
            "traffic_density": 0.1,
            "start_seed": 1000,
            # "manual_control": vis,
            "use_render": False,
            "agent_policy": IDMPolicy,
            "traffic_mode": TrafficMode.Trigger,
            "record_episode": save_episode,
            "map_config": {
                BaseMap.GENERATE_TYPE: MapGenerateMethod.BIG_BLOCK_SEQUENCE,
                BaseMap.GENERATE_CONFIG: "CrCSC",
                BaseMap.LANE_WIDTH: 3.5,
                BaseMap.LANE_NUM: 3,
            }
        }
    )
    try:
        o = env.reset()
        for i in range(1, 100000 if vis else 2000):
            o, r, d, info = env.step([0, 1])
            if vis:
                env.render(mode="top_down", road_color=(35, 35, 35))
            if d:
                epi_info = env.engine.dump_episode("test_dump_single.pkl" if test_dump else None)
                break
        f = open("test_dump_single.pkl", "rb")
        env.config["replay_episode"] = pickle.load(f)
        env.config["record_episode"] = False
        o = env.reset()
        for i in range(1, 100000 if vis else 2000):
            pos = env.engine.replay_manager.get_object_from_agent("default_agent").position
            assert env.vehicle.position == pos
            record_pos = env.engine.replay_manager.current_frame.step_info[
                env.engine.replay_manager.current_frame.agent_to_object("default_agent")]["position"]
            assert np.isclose(np.array(env.vehicle.position), np.array(record_pos[:-1])).all()
            assert abs(env.vehicle.get_z() - record_pos[-1]) < 1e-3
            o, r, d, info = env.step([0, 1])
            if vis:
                env.render(mode="top_down", )
            if info.get("replay_done", False):
                break
    finally:
        env.close()


def test_save_episode_marl(vis=False):
    """
    1. Set record_episode=True to record each episode
    2. dump_episode when done[__all__] == True
    3. You can keep recent episodes
    4. Input episode data to reset() function can replay the episode !
    """

    # setup_logger(True)

    test_dump = True
    dump_recent_episode = 5
    dump_count = 0
    env = MultiAgentRoundaboutEnv(
        dict(use_render=vis, manual_control=False, record_episode=True, horizon=100, force_seed_spawn_manager=True)
    )
    try:
        # Test Record
        o = env.reset(force_seed=1)
        epi_info = None
        # for tt in range(10, 100):
        tt = 13
        print("\nseed: {}\n".format(tt))
        env.engine.spawn_manager.seed(tt)
        o = env.reset()
        for i in range(1, 100000 if vis else 600):
            o, r, d, info = env.step({agent_id: [0, .2] for agent_id in env.vehicles.keys()})
            if vis:
                env.render()
            if d["__all__"]:
                epi_info = env.engine.dump_episode("test_dump.pkl")
                # test dump json
                # if test_dump:
                #     with open("test_dump_{}.json".format(dump_count), "w") as f:
                #         json.dump(epi_info, f)
                #     dump_count += 1
                #     dump_count = dump_count % dump_recent_episode
                break
                # env.reset()

        epi_record = open("test_dump.pkl", "rb")

        # input episode_info to restore
        env.config["replay_episode"] = pickle.load(epi_record)
        env.config["record_episode"] = False
        o = env.reset()
        for i in range(1, 100000 if vis else 2000):
            print("Replay MARL step: {}".format(i))
            o, r, d, info = env.step({agent_id: [0, 0.1] for agent_id in env.vehicles.keys()})
            if vis:
                env.render()
            if d["__all__"]:
                break
    finally:
        env.close()


if __name__ == "__main__":
    test_save_episode(vis=False)
    # test_save_episode_marl(vis=False)
