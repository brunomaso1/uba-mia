import numpy as np
import time

def evaluate_q_table(q_table, env, episodes=100, max_steps=200, render=False):
    total_rewards = []

    for _ in range(episodes):
        state = env.reset()
        episode_reward = 0

        for _ in range(max_steps):
            action = np.argmax(q_table[state])  # Elegir mejor acción
            state, reward, done, _ = env.step(action)
            episode_reward += reward

            if render:
                env.render()
                time.sleep(0.05)

            if done:
                break

        total_rewards.append(episode_reward)

    avg_reward = np.mean(total_rewards)
    return avg_reward