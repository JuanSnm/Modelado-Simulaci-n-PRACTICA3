import os
from pathlib import Path

import yaml
import numpy as np
import matplotlib.pyplot as plt

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


# ======================================================
# CONFIGURACIÓN
# ======================================================

# Carpeta del rosbag. Cambia esta ruta si tu bag se llama de otra forma.
BAG_PATH = "bags/p3_pick_place"

# Carpeta donde se guardarán las gráficas.
OUT_DIR = "bags/p3_pick_place_plots"

# Topic de estados articulares.
JOINT_STATES_TOPIC = "/joint_states"

# En tu robot la IMU está en /imu/data.
# Si cambiaste el bridge para que sea /imu, cambia esto a "/imu".
IMU_TOPIC = "/imu/data"

# Joints de las ruedas.
WHEEL_JOINTS = [
    "wheelA_1_link_joint",
    "wheelA_2_link_joint",
    "wheelA_3_link_joint",
    "wheelB_1_link_joint",
    "wheelB_2_link_joint",
    "wheelB_3_link_joint",
]

# Joints del mecanismo pick and place: brazo + pinza.
PICK_JOINTS = [
    "arm_1_link_joint",
    "arm_2_link_joint",
    "arm_3_link_joint",
    "arm_4_link_joint",
    "gripper_1_link_joint",
    "gripper_2_link_joint",
]


# ======================================================
# ABRIR ROSBAG
# ======================================================

bag_dir = Path(BAG_PATH).resolve()
out_dir = Path(OUT_DIR).resolve()
out_dir.mkdir(parents=True, exist_ok=True)

metadata_path = bag_dir / "metadata.yaml"

if not metadata_path.exists():
    raise FileNotFoundError(f"No encuentro metadata.yaml en {bag_dir}")

with open(metadata_path, "r") as f:
    metadata = yaml.safe_load(f)

storage_id = metadata["rosbag2_bagfile_information"]["storage_identifier"]

reader = rosbag2_py.SequentialReader()
reader.open(
    rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id=storage_id),
    rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    ),
)

# Diccionario: nombre_topic -> tipo_mensaje
topic_types = {}
for topic in reader.get_all_topics_and_types():
    topic_types[topic.name] = topic.type

print("Topics encontrados:")
for name, msg_type in topic_types.items():
    print(f"  {name}: {msg_type}")

if JOINT_STATES_TOPIC not in topic_types:
    raise RuntimeError(f"No existe el topic {JOINT_STATES_TOPIC} en el rosbag")

if IMU_TOPIC not in topic_types:
    raise RuntimeError(f"No existe el topic {IMU_TOPIC} en el rosbag")


# ======================================================
# VARIABLES PARA GUARDAR DATOS
# ======================================================

# Tiempos
t_joint = []
t_imu = []

# Posición de ruedas
wheel_pos = {}
for joint in WHEEL_JOINTS:
    wheel_pos[joint] = []

# Esfuerzos de brazo y pinza
joint_effort = {}
for joint in PICK_JOINTS:
    joint_effort[joint] = []

# Gasto parcial
G_parcial = []

# Aceleraciones IMU
ax = []
ay = []
az = []
a_mod = []

first_time = None


# ======================================================
# LEER MENSAJES DEL ROSBAG
# ======================================================

while reader.has_next():
    topic, data, timestamp = reader.read_next()

    if first_time is None:
        first_time = timestamp

    # Tiempo relativo en segundos
    t = (timestamp - first_time) / 1e9

    # Tipo del mensaje actual
    msg_type = get_message(topic_types[topic])
    msg = deserialize_message(data, msg_type)

    # --------------------------------------------------
    # /joint_states
    # --------------------------------------------------
    if topic == JOINT_STATES_TOPIC:
        t_joint.append(t)

        # Crear diccionario nombre_joint -> posición
        name_to_position = {}
        for i, name in enumerate(msg.name):
            if i < len(msg.position):
                name_to_position[name] = msg.position[i]

        # Crear diccionario nombre_joint -> esfuerzo
        name_to_effort = {}
        for i, name in enumerate(msg.name):
            if i < len(msg.effort):
                name_to_effort[name] = msg.effort[i]

        # Guardar posiciones de ruedas
        for joint in WHEEL_JOINTS:
            if joint in name_to_position:
                wheel_pos[joint].append(name_to_position[joint])
            else:
                wheel_pos[joint].append(np.nan)

        # Calcular gasto parcial
        G_actual = 0.0

        for joint in PICK_JOINTS:
            if joint in name_to_effort:
                effort = name_to_effort[joint]
                joint_effort[joint].append(effort)
                G_actual += abs(effort)
            else:
                joint_effort[joint].append(np.nan)

        G_parcial.append(G_actual)

    # --------------------------------------------------
    # /imu/data
    # --------------------------------------------------
    elif topic == IMU_TOPIC:
        t_imu.append(t)

        ax_i = msg.linear_acceleration.x
        ay_i = msg.linear_acceleration.y
        az_i = msg.linear_acceleration.z

        ax.append(ax_i)
        ay.append(ay_i)
        az.append(az_i)
        a_mod.append(np.sqrt(ax_i**2 + ay_i**2 + az_i**2))


# Convertir listas a arrays de numpy
t_joint = np.array(t_joint)
t_imu = np.array(t_imu)
G_parcial = np.array(G_parcial)
ax = np.array(ax)
ay = np.array(ay)
az = np.array(az)
a_mod = np.array(a_mod)

for joint in WHEEL_JOINTS:
    wheel_pos[joint] = np.array(wheel_pos[joint])

for joint in PICK_JOINTS:
    joint_effort[joint] = np.array(joint_effort[joint])

print(f"\nMensajes /joint_states leídos: {len(t_joint)}")
print(f"Mensajes {IMU_TOPIC} leídos: {len(t_imu)}")


# ======================================================
# GRÁFICA 1: POSICIÓN DE LAS RUEDAS VS TIEMPO
# ======================================================

plt.figure(figsize=(10, 6))

for joint in WHEEL_JOINTS:
    plt.plot(t_joint, wheel_pos[joint], label=joint)

plt.xlabel("Tiempo (s)")
plt.ylabel("Posición de rueda (rad)")
plt.title("Posición de las ruedas vs tiempo")
plt.legend(fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig(out_dir / "01_posicion_ruedas_vs_tiempo.png", dpi=160)
plt.close()


# ======================================================
# GRÁFICA 2: ACELERACIÓN VS TIEMPO
# ======================================================

plt.figure(figsize=(10, 6))

plt.plot(t_imu, ax, label="a_x")
plt.plot(t_imu, ay, label="a_y")
plt.plot(t_imu, az, label="a_z")
plt.plot(t_imu, a_mod, label="|a|")

plt.xlabel("Tiempo (s)")
plt.ylabel("Aceleración (m/s²)")
plt.title("Aceleración vs tiempo")
plt.legend(fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig(out_dir / "02_aceleracion_vs_tiempo.png", dpi=160)
plt.close()


# ======================================================
# GRÁFICA 3: GASTO VS TIEMPO
# ======================================================

G_total = np.sum(G_parcial)
G_std = np.std(G_parcial)

plt.figure(figsize=(10, 6))

plt.plot(t_joint, G_parcial, label="G_parcial", linewidth=2)

# Además se dibuja el esfuerzo absoluto de cada joint del brazo/pinza
for joint in PICK_JOINTS:
    plt.plot(t_joint, np.abs(joint_effort[joint]), alpha=0.45, label=f"|{joint}|")

plt.xlabel("Tiempo (s)")
plt.ylabel("G_parcial")
plt.title(f"Gasto vs tiempo | G_total={G_total:.2f} | std={G_std:.2f}")
plt.legend(fontsize=7)
plt.grid(True)
plt.tight_layout()
plt.savefig(out_dir / "03_gasto_vs_tiempo.png", dpi=160)
plt.close()


# ======================================================
# GUARDAR CSVS OPCIONALES
# ======================================================

# CSV de ruedas
ruedas_csv = out_dir / "datos_ruedas.csv"
ruedas_data = [t_joint]
ruedas_header = "tiempo"

for joint in WHEEL_JOINTS:
    ruedas_data.append(wheel_pos[joint])
    ruedas_header += f",{joint}"

np.savetxt(
    ruedas_csv,
    np.column_stack(ruedas_data),
    delimiter=",",
    header=ruedas_header,
    comments="",
)

# CSV de IMU
imu_csv = out_dir / "datos_imu.csv"
np.savetxt(
    imu_csv,
    np.column_stack([t_imu, ax, ay, az, a_mod]),
    delimiter=",",
    header="tiempo,a_x,a_y,a_z,a_mod",
    comments="",
)

# CSV de gasto
gasto_csv = out_dir / "datos_gasto.csv"
gasto_data = [t_joint, G_parcial]
gasto_header = "tiempo,G_parcial"

for joint in PICK_JOINTS:
    gasto_data.append(np.abs(joint_effort[joint]))
    gasto_header += f",abs_{joint}"

np.savetxt(
    gasto_csv,
    np.column_stack(gasto_data),
    delimiter=",",
    header=gasto_header,
    comments="",
)


print("\nGráficas guardadas en:")
print(out_dir / "01_posicion_ruedas_vs_tiempo.png")
print(out_dir / "02_aceleracion_vs_tiempo.png")
print(out_dir / "03_gasto_vs_tiempo.png")

print("\nCSVs guardados en:")
print(ruedas_csv)
print(imu_csv)
print(gasto_csv)

