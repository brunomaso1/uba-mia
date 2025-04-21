import time
import numpy as np
from utilidades.taxi_env import TaxiEnvCustom, generate_city_blocks, remove_obstacles
from utilidades.generales import clear_or_create_folder
from utilidades.graficar import generar_video
import os
import argparse


def save_step(save_step_path, num):
    env.save_render(img_path=os.path.join(save_step_path, f"step_{num:02}.png"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-render", dest="render", action="store_false")
    parser.add_argument(
        "--video",
        action="store_true",
        help="Genera un video al final con los pasos de la simulación",
    )
    parser.set_defaults(render=True)
    args = parser.parse_args()

    base_dirpath = os.path.dirname(os.path.abspath(__file__)) # ./TP1-QLearning
    results_dirpath = os.path.join(base_dirpath, "results") # ./TP1-QLearning/results
    best_result_dirpath = os.path.join(results_dirpath, "best_result") # ./TP1-QLearning/results/best_result
    q_table_path = os.path.join(results_dirpath, "final_q_table.npy") # ./TP1-QLearning/results/final_q_table.npy
    save_step_dirpath = os.path.join(best_result_dirpath, "img") # ./TP1-QLearning/results/best_result/img
    img_dirpath = os.path.join(base_dirpath, "img") # ./TP1-QLearning/img
    clear_or_create_folder(save_step_dirpath)

    GRID_SIZE = 10
    PICKUP_LOCATIONS = [(1, 1), (8, 7), (4, 2), (2, 8)]
    DROPOFF_LOCATIONS = [(5, 5), (5, 4), (4, 5), (4, 4)]
    OBSTACLES = remove_obstacles(
        generate_city_blocks(GRID_SIZE), PICKUP_LOCATIONS + DROPOFF_LOCATIONS
    )

    env = TaxiEnvCustom(
        GRID_SIZE,
        PICKUP_LOCATIONS,
        DROPOFF_LOCATIONS,
        OBSTACLES,
        img_base_path=img_dirpath,
    )

    if not os.path.exists(q_table_path):
        raise FileNotFoundError(f"No se encontró la Q-table en: {q_table_path}")
    q_table = np.load(q_table_path)

    state = env.reset()
    done = False
    step_number = 0

    if args.render:
        env.render()

    env.save_render(
        img_path=os.path.join(save_step_dirpath, f"step_{step_number:02}.png")
    )

    while not done:
        action = np.argmax(q_table[state])
        state, reward, done, _ = env.step(action)

        if args.render:
            env.render()
            time.sleep(0.1)

        env.save_render(
            img_path=os.path.join(save_step_dirpath, f"step_{step_number:02}.png")
        )
        print(f"Step {step_number} - Reward: {reward}")
        step_number += 1

    if args.video:
        video_path = os.path.join(
            best_result_dirpath, "simulacion.gif"
        )
        generar_video(save_step_dirpath, video_path, fps=5)
        print(f"🎬 Video guardado en: {video_path}")
