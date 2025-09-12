import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# --- Add company logo ---
st.image("logo.png", width=180)  # Place logo.png in same folder

# --- Handy Air-to-Air Plate HEX Sizing Tool ---
st.title("📐 Plate Air-to-Air Heat Exchanger Sizing Tool")
st.write("Handy calculator for sales team: estimate HEX size for given heat load.")

# --- Inputs ---
Q = st.number_input("Heat load (kW)", min_value=0.1, value=5.0, step=0.5) * 1000
T_hot_in = st.number_input("Hot air inlet temp (°C)", value=60.0)
T_cold_in = st.number_input("Cold air inlet temp (°C)", value=30.0)
flow_hot = st.number_input("Hot air flow rate (m³/h)", value=1000.0)
flow_cold = st.number_input("Cold air flow rate (m³/h)", value=1000.0)
eff = st.slider("Assumed effectiveness (%)", 50, 90, 70) / 100

# Plate geometry inputs
plate_length = st.number_input("Plate Width (m)", value=0.5)
plate_height = st.number_input("Plate height (m)", value=0.3)
plate_gap = st.number_input("Plate gap (m)", value=0.003, step=0.001, format="%.3f")

# --- Air properties ---
cp = 1005  # J/kgK
rho = 1.2  # kg/m3

# Mass flow rates
m_hot = flow_hot/3600 * rho
m_cold = flow_cold/3600 * rho

# Capacity rates
C_hot = m_hot * cp
C_cold = m_cold * cp
C_min = min(C_hot, C_cold)

# Max possible heat transfer
Q_max = C_min * (T_hot_in - T_cold_in)

# Realistic heat transfer
Q_calc = min(Q, eff * Q_max)

# LMTD (approx for counterflow)
T_hot_out = T_hot_in - Q_calc/C_hot if C_hot > 0 else T_hot_in
T_cold_out = T_cold_in + Q_calc/C_cold if C_cold > 0 else T_cold_in
dT1 = T_hot_in - T_cold_out
dT2 = T_hot_out - T_cold_in

# Avoid invalid LMTD
if dT1 == dT2 or dT1 <= 0 or dT2 <= 0 or np.isnan(dT1) or np.isnan(dT2):
    LMTD = (dT1 + dT2) / 2 if (dT1 > 0 and dT2 > 0) else np.nan
else:
    LMTD = (dT1 - dT2)/np.log(dT1/dT2)

# Overall U value assumption (W/m²K)
U = 25.0

# Required area & plates
if LMTD <= 0 or np.isnan(LMTD):
    st.error("❌ Invalid temperature difference. Check input conditions.")
    A_req = np.nan
    n_plates = 0
    stack_width = 0
else:
    A_req = Q_calc/(U * LMTD)
    A_plate = plate_length * plate_height
    n_plates = int(np.ceil(A_req / A_plate))
    stack_width = n_plates * plate_gap

    st.subheader("📊 Results")
    st.write(f"Heat duty handled: **{Q_calc/1000:.2f} kW**")
    st.write(f"Hot outlet temp: **{T_hot_out:.1f} °C**")
    st.write(f"Cold outlet temp: **{T_cold_out:.1f} °C**")
    st.write(f"Required heat transfer area: **{A_req:.2f} m²**")
    st.write(f"Suggested plate size: {plate_length:.2f} m × {plate_height:.2f} m")
    st.write(f"Number of plates required: {n_plates}")
    st.write(f"Stack width: {stack_width*1000:.1f} mm")

    # --- Proper 3D Plot ---
    fig = plt.figure(figsize=(10,6))
    ax = fig.add_subplot(111, projection='3d')

    # Draw plates as thin rectangles stacked along X-axis
    for i in range(n_plates):
        color = 'red' if i%2==0 else 'blue'
        x0 = i * plate_gap
        # Rectangle corners (flat plate)
        verts = [
            [(x0, 0, 0), (x0, plate_length, 0), (x0, plate_length, plate_height), (x0, 0, plate_height)],
            [(x0+0.001, 0, 0), (x0+0.001, plate_length, 0), (x0+0.001, plate_length, plate_height), (x0+0.001, 0, plate_height)]
        ]
        ax.add_collection3d(Poly3DCollection(verts, facecolors=color, alpha=0.6, edgecolor='k'))

    # Set aspect ratio for clarity
    max_range = max(stack_width, plate_length, plate_height)
    ax.set_box_aspect([stack_width/max_range, plate_length/max_range, plate_height/max_range])

    # Set view
    ax.view_init(elev=20, azim=-60)

    # Axes labels
    ax.set_xlabel('Stack depth (m)')
    ax.set_ylabel('Plate length (m)')
    ax.set_zlabel('Plate height (m)')
    ax.set_title('3D Schematic: Hot (red) / Cold (blue) Channels')

    st.pyplot(fig)