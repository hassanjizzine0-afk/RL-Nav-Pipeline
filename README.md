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
