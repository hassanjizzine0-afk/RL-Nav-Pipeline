import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/hasan/RL-Nav-Pipeline/ros2_ws/install/navbot_x_bringup'
