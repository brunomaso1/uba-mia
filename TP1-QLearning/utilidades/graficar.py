import matplotlib.pyplot as plt
import numpy as np
import os
import imageio


def generar_video(im_folder, output_path, fps=1):
    images = []
    filenames = sorted([f for f in os.listdir(im_folder) if f.endswith(".png")])
    for filename in filenames:
        img_path = os.path.join(im_folder, filename)
        images.append(imageio.imread(img_path))
    imageio.mimsave(output_path, images, fps=fps)


def plot_learning_curve(rewards, steps=None, success=None, window=100, save_path=None):
    if rewards:
        plt.figure(figsize=(10, 5))
        plt.plot(rewards, label="Reward por episodio", color="tab:blue")
        if len(rewards) >= window:
            rolling_avg = np.convolve(rewards, np.ones(window) / window, mode="valid")
            plt.plot(
                range(window - 1, len(rewards)),
                rolling_avg,
                label=f"Reward media móvil ({window})",
                color="tab:cyan",
            )
        plt.xlabel("Episodio")
        plt.ylabel("Recompensa")
        plt.title("Evolución de la Recompensa")
        plt.legend()
        plt.grid(True)
        if save_path:
            plt.savefig(save_path.replace(".png", "_reward.png"))
            plt.close()
        else:
            plt.show()

    if steps:
        plt.figure(figsize=(10, 5))
        plt.plot(steps, label="Pasos por episodio", color="tab:red", alpha=0.5)
        if len(steps) >= window:
            rolling_steps = np.convolve(steps, np.ones(window) / window, mode="valid")
            plt.plot(
                range(window - 1, len(steps)),
                rolling_steps,
                label=f"Pasos media móvil ({window})",
                color="tab:orange",
            )
        plt.xlabel("Episodio")
        plt.ylabel("Pasos")
        plt.title("Evolución de los Pasos por Episodio")
        plt.legend()
        plt.grid(True)
        if save_path:
            plt.savefig(save_path.replace(".png", "_steps.png"))
            plt.close()
        else:
            plt.show()

    if success:
        plt.figure(figsize=(10, 5))
        if len(success) >= window:
            rolling_success = np.convolve(
                success, np.ones(window) / window, mode="valid"
            )
            plt.plot(
                range(window - 1, len(success)),
                rolling_success,
                label=f"Tasa de éxito ({window})",
                color="tab:green",
                linestyle="--",
            )
        else:
            plt.plot(success, label="Tasa de éxito", color="tab:green", linestyle="--")
        plt.xlabel("Episodio")
        plt.ylabel("Tasa de éxito")
        plt.title("Evolución de la Tasa de Éxito")
        plt.legend()
        plt.grid(True)
        if save_path:
            plt.savefig(save_path.replace(".png", "_success.png"))
            plt.close()
        else:
            plt.show()


def plot_study_results(study, save_dir):
    trials = study.trials
    trial_nums = [t.number for t in trials]
    rewards = [t.value for t in trials]
    alphas = [t.params["alpha"] for t in trials]
    gammas = [t.params["gamma"] for t in trials]
    epsilons = [t.params["epsilon"] for t in trials]

    # Gráfico de convergencia sin filtrar
    plt.figure(figsize=(10, 5))
    plt.plot(trial_nums, rewards, marker="o")
    plt.xlabel("Trial")
    plt.ylabel("Recompensa promedio")
    plt.title("Convergencia del estudio Optuna")
    plt.grid(True)
    plt.savefig(os.path.join(save_dir, "optuna_convergencia.png"))
    plt.close()

    # Gráfico de convergencia filtrando outliers negativos
    trial_nums_filt = [n for n, r in zip(trial_nums, rewards) if r > -200]
    rewards_filt = [r for r in rewards if r > -200]
    plt.figure(figsize=(10, 5))
    plt.plot(trial_nums_filt, rewards_filt, marker="o", color="tab:blue")
    plt.xlabel("Trial")
    plt.ylabel("Recompensa promedio")
    plt.title("Convergencia (sin outliers extremos)")
    plt.grid(True)
    plt.savefig(os.path.join(save_dir, "optuna_convergencia_filtrada.png"))
    plt.close()

    # Escala de color según número de trial (más oscuro = más reciente)
    cmap = plt.colormaps.get_cmap("viridis")
    norm = plt.Normalize(min(trial_nums), max(trial_nums))

    for param_name, param_values in zip(
        ["alpha", "gamma", "epsilon"], [alphas, gammas, epsilons]
    ):
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = [cmap(norm(n)) for n in trial_nums]
        scatter = ax.scatter(param_values, rewards, c=colors, edgecolor="black")
        ax.set_xlabel(param_name)
        ax.set_ylabel("Recompensa promedio")
        ax.set_title(f"Importancia de {param_name} (color según número de trial)")
        ax.grid(True)

        # Agregar barra de color correctamente asociada al eje
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax)
        cbar.set_label("Número de Trial")

        plt.savefig(os.path.join(save_dir, f"optuna_param_{param_name}.png"))
        plt.close(fig)
