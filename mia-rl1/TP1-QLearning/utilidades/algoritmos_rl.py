import numpy as np

def q_learning(alpha, gamma, epsilon, env, episodes=1000, graficar_aprendizaje=False, epsilon_decay_rate=None):
    """Entrena un agente Q-Learning con los hiperparámetros dados."""
    q_table = np.zeros((env.state_space, env.action_space))
    total_rewards = []
    steps_per_episode = []
    success_per_episode = []
    max_epsilon = 1.0
    min_epsilon = 0.01

    for ep in range(episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        success = 0

        for _ in range(200):  # Limitar a 200 pasos por episodio
            if np.random.uniform(0, 1) < epsilon:
                action = np.random.randint(0, env.action_space)
            else:
                action = np.argmax(q_table[state])

            # Tomar acción y observar el siguiente estado y recompensa
            next_state, reward, done, _ = env.step(action)
            
            # Actualizar la Q-table usando la fórmula de Q-Learning
            q_value_current_state = q_table[state, action]
            max_q_value_next_state = np.max(q_table[next_state])
            td_target = reward + gamma * max_q_value_next_state # TD: Temporal Difference
            td_error = td_target - q_value_current_state
            q_table[state, action] = q_value_current_state + (alpha * td_error)
            
            # Actualizar el estado actual
            state = next_state
            total_reward += reward
            steps += 1

            if done:
                success = 1
                break

        total_rewards.append(total_reward)
        steps_per_episode.append(steps)
        success_per_episode.append(success)

        # Actualizar epsilon si se proporciona una tasa de decaimiento
        if epsilon_decay_rate:
            epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-epsilon_decay_rate * ep)

    # Calcular la recompensa promedio de los últimos 100 episodios
    avg_reward = np.mean(total_rewards[-100:])

    if graficar_aprendizaje:
        return avg_reward, q_table, total_rewards, steps_per_episode, success_per_episode
    else:
        return avg_reward, q_table