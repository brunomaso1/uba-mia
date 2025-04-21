import random
import pygame
import os


def generate_city_blocks(GRID_SIZE):
    obstacles = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if row % 3 == 0 or col % 3 == 0:
                continue
            obstacles.append((row, col))
    return obstacles


def remove_obstacles(obstacles, to_remove):
    """Elimina de la lista de obstáculos los puntos especificados en to_remove."""
    return [pos for pos in obstacles if pos not in to_remove]


class TaxiEnvCustom:
    def __init__(
        self,
        GRID_SIZE,
        PICKUP_LOCATIONS,
        DROPOFF_LOCATIONS,
        OBSTACLES,
        img_base_path=None,
    ):
        self.img_base_path = img_base_path
        self.grid_size = GRID_SIZE
        self.pickups = PICKUP_LOCATIONS
        self.dropoffs = DROPOFF_LOCATIONS
        self.obstacles = OBSTACLES
        self.state_space = GRID_SIZE * GRID_SIZE * len(self.pickups) * 2
        self.action_space = 6
        self.last_action = None  # Inicializar la última acción como None
        self.pickup_colors = None
        self.in_taxi = 0  # 0: no en taxi, 1: en taxi
        self.done = False
        self.valid_positions = [
            (r, c)
            for r in range(self.grid_size)
            for c in range(self.grid_size)
            if (r, c) not in self.obstacles
            and (r, c) not in self.pickups
            and (r, c) not in self.dropoffs
        ]
        self.reset()

    def action_space_sample(self):
        """Devuelve una acción aleatoria dentro del espacio de acciones."""
        return random.randint(0, self.action_space - 1)

    def encode(self, taxi_row, taxi_col, passenger_idx, in_taxi):
        """Codifica el estado en un número entero único."""
        return (
            (taxi_row * self.grid_size + taxi_col) * len(self.pickups) + passenger_idx
        ) * 2 + in_taxi

    def decode(self, state):
        """Decodifica el número entero único del estado en sus componentes."""
        in_taxi = state % 2
        state //= 2
        passenger_idx = state % len(self.pickups)
        state //= len(self.pickups)
        taxi_col = state % self.grid_size
        taxi_row = state // self.grid_size
        return taxi_row, taxi_col, passenger_idx, in_taxi

    def reset(self):
        self.taxi_row, self.taxi_col = random.choice(self.valid_positions)
        self.passenger_idx = random.randint(0, len(self.pickups) - 1)
        self.in_taxi = 0
        return self.encode(
            self.taxi_row, self.taxi_col, self.passenger_idx, self.in_taxi
        )

    def step(self, action):
        """Realiza un paso en el entorno según la acción dada."""
        reward = -1  # penalización base por movimiento
        done = False

        # Obtener la posición actual del taxi
        next_row, next_col = self.taxi_row, self.taxi_col

        # Obtener la posición luego de realizar la acción
        if action == 0 and self.taxi_row < self.grid_size - 1:  # mover hacia abajo
            next_row += 1
        elif action == 1 and self.taxi_row > 0:  # mover hacia arriba
            next_row -= 1
        elif action == 2 and self.taxi_col < self.grid_size - 1:  # mover a la derecha
            next_col += 1
        elif action == 3 and self.taxi_col > 0:  # mover a la izquierda
            next_col -= 1

        # Verificar si el taxi está actualmente en un pickup o dropoff
        en_pickup_o_dropoff = (self.taxi_row, self.taxi_col) in self.pickups or (
            self.taxi_row,
            self.taxi_col,
        ) in self.dropoffs

        # Penalizar si el movimiento va contra el sentido de la calle, salvo si está en pickup o dropoff
        street_direction = self.get_street_direction(next_row, next_col)
        if street_direction and not en_pickup_o_dropoff:
            if (
                (action == 0 and street_direction != "down")
                or (action == 1 and street_direction != "up")
                or (action == 2 and street_direction != "right")
                or (action == 3 and street_direction != "left")
            ):
                reward -= 5

        # Realizar el movimiento si no hay obstáculos
        if (next_row, next_col) not in self.obstacles:
            self.taxi_row, self.taxi_col = next_row, next_col

        # Penalizar si el taxi se mueve a una posición dropoff sin pasajero
        if (self.taxi_row, self.taxi_col) in self.dropoffs and not self.in_taxi:
            reward -= 5
        
        # Levanta al pasajero si está en la posición de recogida, sino penaliza levantar un fantasma...
        # Lo mismo para dejarlo, recompensa si lo deja en la posición de entrega correcta, sino penaliza dejarlo en un lugar incorrecto.
        if action == 4:
            if (
                not self.in_taxi
                and (self.taxi_row, self.taxi_col) == self.pickups[self.passenger_idx]
            ):
                self.in_taxi = 1
                reward = 15
            else:
                reward = -15
        elif action == 5:
            if self.in_taxi and (self.taxi_row, self.taxi_col) in self.dropoffs:
                self.in_taxi = 0
                reward = 30
                done = True
                self.done = done
            else:
                reward = -15

        self.last_action = action

        # Obtengo el siguiente estado.
        next_state = self.encode(
            self.taxi_row, self.taxi_col, self.passenger_idx, self.in_taxi
        )
        return next_state, reward, done, {}

    def render(self):
        # Inicializar pygame si no está inicializado
        if not hasattr(self, "window"):
            pygame.init()
            self.cell_size = 50  # Tamaño de cada celda en píxeles
            self.window_size = (
                self.grid_size * self.cell_size,
                self.grid_size * self.cell_size,
            )
            self.window = pygame.display.set_mode(self.window_size)
            self.clock = pygame.time.Clock()

            base_path = self.img_base_path
            img_background = os.path.join(base_path, "taxi_background.png")
            img_obstacle_horizontal = os.path.join(
                base_path, "gridworld_median_horiz.png"
            )
            img_obstacle_horizontal_last = os.path.join(
                base_path, "gridworld_median_right.png"
            )
            img_obstacle_horizontal_first = os.path.join(
                base_path, "gridworld_median_left.png"
            )
            img_obstacle_vertical = os.path.join(base_path, "gridworld_median_vert.png")
            img_obstacle_vertical_first = os.path.join(
                base_path, "gridworld_median_top.png"
            )
            img_obstacle_vertical_last = os.path.join(
                base_path, "gridworld_median_bottom.png"
            )
            img_obstacle = os.path.join(base_path, "gridworld_median_horiz.png")
            img_passenger = os.path.join(base_path, "passenger.png")
            img_dropoff = os.path.join(base_path, "dropoff.png")

            # Cargar la imagen de fondo
            self.background_image = pygame.transform.scale(
                pygame.image.load(img_background), self.window_size
            )

            # Cargar otras imágenes si no están cargadas
            self.images = {
                "obstacle_horizontal_first": pygame.transform.scale(
                    pygame.image.load(img_obstacle_horizontal_first),
                    (self.cell_size, self.cell_size),
                ),
                "obstacle_horizontal_last": pygame.transform.scale(
                    pygame.image.load(img_obstacle_horizontal_last),
                    (self.cell_size, self.cell_size),
                ),
                "obstacle_horizontal": pygame.transform.scale(
                    pygame.image.load(img_obstacle_horizontal),
                    (self.cell_size, self.cell_size),
                ),
                "obstacle_vertical_first": pygame.transform.scale(
                    pygame.image.load(img_obstacle_vertical_first),
                    (self.cell_size, self.cell_size),
                ),
                "obstacle_vertical_last": pygame.transform.scale(
                    pygame.image.load(img_obstacle_vertical_last),
                    (self.cell_size, self.cell_size),
                ),
                "obstacle_vertical": pygame.transform.scale(
                    pygame.image.load(img_obstacle_vertical),
                    (self.cell_size, self.cell_size),
                ),
                "obstacle": pygame.transform.scale(
                    pygame.image.load(img_obstacle), (self.cell_size, self.cell_size)
                ),
                "passenger": pygame.transform.scale(
                    pygame.image.load(img_passenger), (self.cell_size, self.cell_size)
                ),
                "dropoff": pygame.transform.scale(
                    pygame.image.load(img_dropoff), (self.cell_size, self.cell_size)
                ),
            }

            # Cargar la imagen del taxi
            img_taxi_up = os.path.join(base_path, "taxi_up.png")
            img_taxi_down = os.path.join(base_path, "taxi_down.png")
            img_taxi_left = os.path.join(base_path, "taxi_left.png")
            img_taxi_right = os.path.join(base_path, "taxi_right.png")

            self.taxi_images = {
                "up": pygame.transform.scale(
                    pygame.image.load(img_taxi_up), (self.cell_size, self.cell_size)
                ),
                "down": pygame.transform.scale(
                    pygame.image.load(img_taxi_down), (self.cell_size, self.cell_size)
                ),
                "left": pygame.transform.scale(
                    pygame.image.load(img_taxi_left), (self.cell_size, self.cell_size)
                ),
                "right": pygame.transform.scale(
                    pygame.image.load(img_taxi_right), (self.cell_size, self.cell_size)
                ),
            }

        # Dibujar la imagen de fondo
        self.window.blit(self.background_image, (0, 0))

        # Dibujar la cuadrícula (opcional, si quieres mantener las líneas de la cuadrícula)
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                rect = pygame.Rect(
                    col * self.cell_size,
                    row * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(
                    self.window, (200, 200, 200), rect, 1
                )  # Bordes de la celda

        # Dibujar los obstáculos
        for i, (r, c) in enumerate(self.obstacles):
            # Determinar si el obstáculo es parte de un grupo horizontal o vertical
            is_horizontal = False
            is_vertical = False

            # Verificar si el obstáculo es parte de un grupo horizontal
            if (
                i > 0
                and self.obstacles[i - 1][0] == r
                and self.obstacles[i - 1][1] == c - 1
            ):
                is_horizontal = True
            if (
                i < len(self.obstacles) - 1
                and self.obstacles[i + 1][0] == r
                and self.obstacles[i + 1][1] == c + 1
            ):
                is_horizontal = True

            # Verificar si el obstáculo es parte de un grupo vertical
            if (
                i > 0
                and self.obstacles[i - 1][1] == c
                and self.obstacles[i - 1][0] == r - 1
            ):
                is_vertical = True
            if (
                i < len(self.obstacles) - 1
                and self.obstacles[i + 1][1] == c
                and self.obstacles[i + 1][0] == r + 1
            ):
                is_vertical = True

            # Dibujar el obstáculo según su tipo
            if is_horizontal and not is_vertical:
                # Es parte de un grupo horizontal
                if (
                    i > 0
                    and self.obstacles[i - 1][0] == r
                    and self.obstacles[i - 1][1] == c - 1
                    and (
                        i == len(self.obstacles) - 1
                        or self.obstacles[i + 1][0] != r
                        or self.obstacles[i + 1][1] != c + 1
                    )
                ):
                    # Último en el grupo horizontal
                    self.window.blit(
                        self.images["obstacle_horizontal_last"],
                        (c * self.cell_size, r * self.cell_size),
                    )
                elif (
                    i < len(self.obstacles) - 1
                    and self.obstacles[i + 1][0] == r
                    and self.obstacles[i + 1][1] == c + 1
                    and (
                        i == 0
                        or self.obstacles[i - 1][0] != r
                        or self.obstacles[i - 1][1] != c - 1
                    )
                ):
                    # Primero en el grupo horizontal
                    self.window.blit(
                        self.images["obstacle_horizontal_first"],
                        (c * self.cell_size, r * self.cell_size),
                    )
                else:
                    # Intermedio en el grupo horizontal
                    self.window.blit(
                        self.images["obstacle_horizontal"],
                        (c * self.cell_size, r * self.cell_size),
                    )
            elif is_vertical and not is_horizontal:
                # Es parte de un grupo vertical
                if (
                    i > 0
                    and self.obstacles[i - 1][1] == c
                    and self.obstacles[i - 1][0] == r - 1
                    and (
                        i == len(self.obstacles) - 1
                        or self.obstacles[i + 1][1] != c
                        or self.obstacles[i + 1][0] != r + 1
                    )
                ):
                    # Último en el grupo vertical
                    self.window.blit(
                        self.images["obstacle_vertical_last"],
                        (c * self.cell_size, r * self.cell_size),
                    )
                elif (
                    i < len(self.obstacles) - 1
                    and self.obstacles[i + 1][1] == c
                    and self.obstacles[i + 1][0] == r + 1
                    and (
                        i == 0
                        or self.obstacles[i - 1][1] != c
                        or self.obstacles[i - 1][0] != r - 1
                    )
                ):
                    # Primero en el grupo vertical
                    self.window.blit(
                        self.images["obstacle_vertical_first"],
                        (c * self.cell_size, r * self.cell_size),
                    )
                else:
                    # Intermedio en el grupo vertical
                    self.window.blit(
                        self.images["obstacle_vertical"],
                        (c * self.cell_size, r * self.cell_size),
                    )
            else:
                # Obstáculo aislado
                self.window.blit(
                    self.images["obstacle"], (c * self.cell_size, r * self.cell_size)
                )

        # Dibujar las flechas de orientación de calles
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                direction = self.get_street_direction(row, col)
                if direction:
                    center_x = col * self.cell_size + self.cell_size // 2
                    center_y = row * self.cell_size + self.cell_size // 2
                    size = self.cell_size // 3

                    if direction == "up":
                        points = [
                            (center_x, center_y - size),
                            (center_x - size, center_y + size),
                            (center_x + size, center_y + size),
                        ]
                    elif direction == "down":
                        points = [
                            (center_x, center_y + size),
                            (center_x - size, center_y - size),
                            (center_x + size, center_y - size),
                        ]
                    elif direction == "left":
                        points = [
                            (center_x - size, center_y),
                            (center_x + size, center_y - size),
                            (center_x + size, center_y + size),
                        ]
                    elif direction == "right":
                        points = [
                            (center_x + size, center_y),
                            (center_x - size, center_y - size),
                            (center_x - size, center_y + size),
                        ]

                    pygame.draw.polygon(self.window, (255, 0, 0), points)

        # Dibujar los puntos de recogida con fondo de color distinto
        for r, c in self.pickups:
            rect = pygame.Rect(
                c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size
            )
            pygame.draw.rect(
                self.window, (173, 216, 230), rect
            )  # Fondo azul claro para puntos de recogida

        # Dibujar al pasajero si no está en el taxi
        if not self.in_taxi and not self.done:
            passenger_row, passenger_col = self.pickups[self.passenger_idx]
            self.window.blit(
                self.images["passenger"],
                (passenger_col * self.cell_size, passenger_row * self.cell_size),
            )

        # Dibujar los puntos de entrega
        for r, c in self.dropoffs:
            self.window.blit(
                self.images["dropoff"], (c * self.cell_size, r * self.cell_size)
            )

        # Dibujar el taxi
        if self.last_action == 0:  # Abajo
            taxi_image = self.taxi_images["down"]
        elif self.last_action == 1:  # Arriba
            taxi_image = self.taxi_images["up"]
        elif self.last_action == 2:  # Derecha
            taxi_image = self.taxi_images["right"]
        elif self.last_action == 3:  # Izquierda
            taxi_image = self.taxi_images["left"]
        else:  # Acción inicial o desconocida
            taxi_image = self.taxi_images["down"]

        self.window.blit(
            taxi_image, (self.taxi_col * self.cell_size, self.taxi_row * self.cell_size)
        )

        # Actualizar la pantalla
        pygame.display.flip()

        # Manejar eventos de pygame para evitar que la ventana se congele
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

    def save_render(self, img_path):
        """Guarda la imagen renderizada actual en el archivo especificado."""
        pygame.image.save(self.window, img_path)

    def get_street_direction(self, row, col):
        # Si estamos sobre una calle horizontal (fila múltiplo de 3)
        if row % 3 == 0 and col % 3 != 0:
            if (row // 3) % 2 == 0:
                return "right"  # circulación → derecha
            else:
                return "left"  # circulación → izquierda

        # Si estamos sobre una calle vertical (columna múltiplo de 3)
        if col % 3 == 0 and row % 3 != 0:
            if (col // 3) % 2 == 0:
                return "up"  # circulación ↓ abajo
            else:
                return "down"  # circulación ↑ arriba

        return None  # dentro de manzana o intersección
