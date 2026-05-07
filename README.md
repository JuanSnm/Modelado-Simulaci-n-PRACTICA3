# Modelado-Simulación-PRACTICA3

El objetivo de esta práctica ha sido realizar la simulación y el análisis de un robot móvil manipulador en Gazebo utilizando ROS2 y MoveIt2. Para ello, se ha empleado el robot desarrollado en prácticas anteriores, compuesto por una base móvil con ruedas y un brazo manipulador tipo SCARA con pinza.

Durante la práctica se ha configurado el sistema completo de simulación, incluyendo el modelo del robot, los controladores, la integración con Gazebo, la visualización en RViz y la planificación de movimientos mediante MoveIt 2. La base móvil se ha controlado mediante comandos de velocidad publicados en el topic `/cmd_vel`, mientras que el brazo y la pinza se han teleoperado desde la interfaz de planificación de MoveIt 2.

## COMANDOS

Para ejecutar la simulación completa se utilizaron varias terminales, todas ellas situadas en la raíz del workspace de la práctica:

```bash
cd ~/p3
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

### 1. Lanzamiento del robot, Gazebo, RViz y controladores `TERMINAL_1`

```bash
ros2 launch rover_description robot.launch.py use_jsp_gui:=false launch_controllers:=true
```
Este comando inicia la simulación en Gazebo, carga el modelo del robot, publica el estado del robot y lanza los controladores definidos para la base móvil, el brazo manipulador y la pinza.

### 2. Lanzamiento de MoveIt 2 `TERMINAL_2`

```bash
ros2 launch rover_moveit_config move_group.launch.py use_sim_time:=true
```
Este nodo permite realizar la planificación y ejecución de movimientos del brazo y la pinza desde RViz mediante el plugin MotionPlanning.

### 3. Teleoperación de la base móvil `TERMINAL_3`

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
Para controlar la base móvil se utilizó el paquete `teleop_twist_keyboard`, que publica comandos de velocidad en el topic `/cmd_vel`.

### 4. Grabación del rosbag `TERMINAL_4`

```bash
ros2 bag record --use-sim-time -o bags/p3_pick_place /cmd_vel /imu/data /joint_states
```
En esta implementación, la IMU está publicada en el topic `/imu/data`. Este topic contiene la información equivalente requerida por el enunciado para la aceleración del robot. El rosbag incluye los datos de velocidad de la base, aceleración de la IMU y estados articulares del robot.

### 5. Generación de gráficas

```bash
python3 plot_results.py
```
Finalmente, se ejecutó el script de análisis para leer el rosbag y generar las tres gráficas solicitadas.

## DESARROLLO

### Arbol de transformadas

El árbol de transformadas del robot se ha generado mediante la herramienta `view_frames` de ROS2. Este árbol permite visualizar la relación jerárquica entre los distintos sistemas de referencia del robot, partiendo del frame principal `base_footprint` y conectando los enlaces de la base, las ruedas, el brazo manipulador, la pinza, la IMU y las cámaras.

[arbol_transformadas.pdf](https://github.com/user-attachments/files/27489821/arbol_transformadas.pdf)

En el árbol se observa que `base_footprint` actúa como referencia principal del robot. A partir de él se publican las transformadas hacia `base_link`, los enlaces de las ruedas, el sensor IMU, las cámaras y la cadena cinemática del manipulador formada por `arm_1_link`, `arm_2_link`, `arm_3_link`, `arm_4_link`, `base_endEffector_link` y los enlaces de la pinza que son `gripper_1_link` y `gripper_2_link`. El árbol generado confirma que todos los links principales del robot están correctamente conectados dentro del sistema TF.

### Captura de RViz

<img width="1748" height="1027" alt="captura_rviz" src="https://github.com/user-attachments/assets/94151d30-7ed3-4cf1-8088-c257bf3703b5" />


### Explicación detallada de las gráficas generadas 

#### Posición_ruedas vs Tiempo
<img width="1600" height="960" alt="01_posicion_ruedas_vs_tiempo" src="https://github.com/user-attachments/assets/14bca0e6-c05d-4311-a98d-9a7e9701051e" />


#### Aceleración vs Tiempo
<img width="1600" height="960" alt="02_aceleracion_vs_tiempo" src="https://github.com/user-attachments/assets/16c32585-f7f8-435a-871e-21615574d9cd" />


#### Gasto vs Tiempo
<img width="1600" height="960" alt="03_gasto_vs_tiempo" src="https://github.com/user-attachments/assets/81031340-453d-422b-8956-1790321490a0" />






### Video de simulación 

En lugar de tener imagenes individuales de la simulación, podemos observar todo el proceso de la simulación que dan como resultado nuestra gráficas (vistas anteriormente):








