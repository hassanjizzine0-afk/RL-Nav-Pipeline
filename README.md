#  RL-Nav-Pipeline: Autonomous AMR Navigation via Reinforcement Learning

##  О проекте
Этот проект — полный пайплайн для обучения автономного мобильного робота (AMR) навигации в симуляторе с использованием глубокого обучения с подкреплением (Deep RL).

В отличие от классических алгоритмов SLAM, здесь робот учится избегать препятствий и достигать цели методом проб и ошибок, используя данные лидара.

##  Архитектура системы
Проект состоит из двух основных частей:
1. **Симуляция (ROS 2 + Gazebo):** Виртуальный мир, модель робота (URDF), лидар, мосты связи (`ros_gz`).
2. **Мозг (Python + Gymnasium + Stable-Baselines3):** Среда обучения (Environment), которая переводит данные ROS 2 в формат нейросети и обратно, а также алгоритм PPO для обучения.

##  Технологический стек
- **OS:** Ubuntu 24.04
- **Middleware:** ROS 2 Jazzy
- **Simulator:** Gazebo Sim (ros_gz)
- **Language:** Python 3.12
- **RL Framework:** Gymnasium
- **RL Algorithm:** PPO
- **Training Library:** Stable-Baselines3

##  Как это работает (Цикл обучения)
1. Нейросеть (PPO) получает данные с лидара (`/scan`) и одометрии (`/odom`).
2. Принимает решение о скорости и повороте.
3. Отправляет команду в `/cmd_vel`.
4. Робот двигается в Gazebo.
5. Среда (Environment) вычисляет награду (Reward): плюс за движение к цели, минус за столкновение.
6. Нейросеть обновляет свои веса, чтобы в следующий раз получить больше награды.


.

## 📁 Структура проекта

```text
RL-Nav-Pipeline/
│
├── ros2_ws/                          # ROS 2 workspace (собирается colcon)
│   └── src/
│       └── navbot_x_rl_navigation/   # пакеты симуляции (клонированы)
│           ├── navbot_x_bringup/     # launch-файлы: spawn + bridge
│           ├── navbot_x_description/ # URDF, меши, сенсоры (лидар)
│           └── navbot_x_gazebo/      # миры Gazebo, препятствия
│
├── rl/                               # Python-часть (RL-мозг)
│   ├── env/
│   │   └── navbot_env.py             # Gymnasium-среда NavBotEnv
│   ├── train/
│   │   └── train_ppo.py              # скрипт запуска обучения PPO
│   ├── utils/
│   │   ├── ros_bridge.py             # обёртка над rclpy (pub/sub)
│   │   └── reward.py                 # функции награды
│   └── configs/
│       └── ppo_config.yaml           # гиперпараметры PPO, среда
│
├── models/                           # сохранённые веса политик (.zip)
├── logs/                             # TensorBoard-логи, метрики обучения
├── configs/                          # общие конфиги (мир, робот, задачи)
├── docs/                             # схемы архитектуры, отчёты
├── scripts/                          # вспомогательные bash-скрипты
│   ├── run_sim.sh                    # терминал 1
│   ├── run_bridge.sh                 # терминал 2
│   └── run_train.sh                  # терминал 3
│
├── requirements.txt                  # Python-зависимости (sb3, gymnasium…)
├── .gitignore
└── README.md
```

###  Поток данных (data flow)

```text
[Лидар /scan] ──┐
                ├──► NavBotEnv (Gymnasium) ──► PPO (нейросеть)
[Одометрия /odom]┘         │                        │
                           │   reward = f(goal,     │ action
                           │   collision, progress) │ (v, ω)
                           ▼                        ▼
                    [TensorBoard]            [/cmd_vel] ──► Gazebo
```

###  Три терминала (запуск)

| # | Роль               | Команда                      |
|---|--------------------|------------------------------|
| 1 | Симуляция          | `bash scripts/run_sim.sh`    |
| 2 | Мосты ROS ↔ Gazebo | `bash scripts/run_bridge.sh` |
| 3 | Обучение PPO       | `bash scripts/run_train.sh`  |

```
┌─────────────────────────────────────────────────────────────┐
│ Gazebo (gz-transport)                                       │
│  URDF: visual, collision, <sensor>, <plugin>                │
│  плагины публикуют: gz.msgs.LaserScan, gz.msgs.Odometry     │
└──────────────────────────┬──────────────────────────────────┘
                           │ gz-топики (сырые)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ros_gz_bridge  (отдельный процесс, терминал 2)              │
│  gz.msgs.LaserScan → sensor_msgs/LaserScan → /scan          │
│  gz.msgs.Odometry  → nav_msgs/Odometry     → /odom          │
│  /cmd_vel (Twist)  → gz.msgs.Twist         → Gazebo         │
└──────────────────────────┬──────────────────────────────────┘
                           │ ROS 2 топики /scan, /odom
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ RosBridge  (Python-нода внутри train_ppo.py)                │
│  подписка /scan, /odom → latest_scan, latest_pose           │
│  паблишер /cmd_vel ← publish_cmd_vel(v, ω)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ numpy-массивы
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ NavBotEnv (Gymnasium)                                       │
│  _get_observation():                                        │
│    scan(360) + pose(x,y,yaw,dist) → obs (364,)              │
│                                                             │
│  step(action):                                              │
│    1. bridge.publish_cmd_vel(v, ω)  ──┐                     │
│    2. obs = _get_observation()        │                     │
│    3. reward, terminated = compute_reward(...)              │
│    4. return obs, reward, term, trunc, info                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ (obs, reward, terminated, truncated)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ PPO (Stable-Baselines3, MlpPolicy)                          │
│  вход: 364 числа → скрытые слои → выход: 2 числа (v, ω)     │
│                                                             │
│  цикл обучения:                                             │
│    action = model.predict(obs)                              │
│    obs, r, term, trunc, _ = env.step(action)                │
│    сохранить (obs, action, r) в rollout buffer              │
│    каждые n_steps → обновить веса PPO                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ action (v, ω)
                           └──────────────► обратно в NavBotEnv.step()
                                            → publish_cmd_vel
                                            → /cmd_vel
                                            → ros_gz_bridge
                                            → Gazebo




```


###  Три терминала (запуск)

| # | Роль               | Команда                      |
|---|--------------------|------------------------------|
| 1 | Симуляция          | `bash scripts/run_sim.sh`    |
| 2 | Мосты ROS ↔ Gazebo | `bash scripts/run_bridge.sh` |
| 3 | Обучение PPO       | `bash scripts/run_train.sh`  |




**Терминал 1 — Симуляция:**
```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 launch navbot_x_bringup spawn_navbot.launch.py
```

**Терминал 2 — Мосты:**
```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 launch navbot_x_bringup bridge.launch.py
```

**Терминал 3 — Обучение:**
```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
source venv/bin/activate
python3 -m rl.train.train_ppo
```

## Структура
```
ros2_ws/   # Gazebo, URDF, миры
rl/        # env, train, utils, configs
models/    # веса .zip
logs/      # TensorBoard
venv/      # Python-окружение
```

```
