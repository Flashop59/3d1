import streamlit as st
import trimesh
import numpy as np
import plotly.graph_objects as go
import tempfile

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="3D Print Weight Estimator", layout="wide", page_icon="🧊")

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ 3D VISUALIZATION ------------------
def show_stl(uploaded_file):
    """Display STL model interactively using Plotly."""
    try:
        mesh = trimesh.load(uploaded_file)
        vertices = mesh.vertices
        faces = mesh.faces

        fig = go.Figure(
            data=[
                go.Mesh3d(
                    x=vertices[:, 0],
                    y=vertices[:, 1],
                    z=vertices[:, 2],
                    i=faces[:, 0],
                    j=faces[:, 1],
                    k=faces[:, 2],
                    color="lightblue",
                    opacity=0.6,
                )
            ]
        )

        fig.update_layout(
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="black",
            scene_aspectmode="data",
        )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ Could not visualize STL: {e}")

# ------------------ WEIGHT CALCULATION ------------------
def calculate_weight(stl_file, params):
    """Estimate print weight based on STL geometry and user settings."""
    try:
        mesh = trimesh.load(stl_file)
        volume_cm3 = mesh.volume / 1000  # mm³ → cm³

        density = params["material_density"]
        infill = params["infill_density"] / 100.0
        wall_thickness = params["wall_thickness"]
        top_bottom = params["top_bottom_thickness"]
        layer_height = params["layer_height"]

        # Empirical modifiers for accuracy
        shell_factor = 1 + (wall_thickness / 2.0) * (1 - infill)
        top_bottom_factor = 1 + (top_bottom / 5.0) * (1 - infill)

        adjusted_volume = volume_cm3 * (0.1 + 0.7 * infill + 0.2 * shell_factor * top_bottom_factor)
        weight = adjusted_volume * density

        return round(weight, 2)
    except Exception as e:
        st.error(f"Error estimating weight: {e}")
        return None

# ------------------ MATERIALS & PATTERNS ------------------
materials = {
    "PLA": 1.24,
    "ABS": 1.04,
    "PETG": 1.27,
    "Nylon": 1.15,
    "TPU": 1.21
}

infill_patterns = ["Grid", "Gyroid", "Cubic", "Triangles", "Honeycomb"]

# ------------------ UI ------------------
st.title("🧊 3D Print Weight Estimator")
mode = st.radio("Select Mode:", ["Basic", "Advanced"], horizontal=True)

uploaded_file = st.file_uploader("📁 Upload your STL file", type=["stl"])

if uploaded_file:
    st.success("✅ STL file uploaded successfully!")
    show_stl(uploaded_file)

# ------------------ BASIC MODE ------------------
if mode == "Basic":
    st.header("🟢 Basic Mode")

    col1, col2 = st.columns(2)
    with col1:
        material = st.selectbox("Material", list(materials.keys()), index=0)
        infill_density = st.slider("Infill Density (%)", 0, 100, 20)
        infill_pattern = st.selectbox("Infill Pattern", infill_patterns, index=0)
    with col2:
        layer_height = st.number_input("Layer Height (mm)", 0.05, 0.4, 0.3, step=0.05)
        wall_thickness = st.number_input("Wall Thickness (mm)", 0.4, 3.0, 1.2, step=0.1)
        top_bottom_thickness = st.number_input("Top/Bottom Thickness (mm)", 0.4, 3.0, 0.8, step=0.1)
        support = st.checkbox("Generate Support", value=False)

    params = {
        "material_density": materials[material],
        "infill_density": infill_density,
        "wall_thickness": wall_thickness,
        "top_bottom_thickness": top_bottom_thickness,
        "layer_height": layer_height,
        "support": support,
    }

    if st.button("🔍 Estimate Print Weight"):
        if uploaded_file is None:
            st.warning("Please upload an STL file first.")
        else:
            weight = calculate_weight(uploaded_file, params)
            if weight:
                st.markdown("### 🧱 Estimated Print Weight")
                st.subheader(f"Approximate Weight: **{weight} g**")

# ------------------ ADVANCED MODE ------------------
if mode == "Advanced":
    st.header("🔵 Advanced Mode")

    col1, col2, col3 = st.columns(3)
    with col1:
        material = st.selectbox("Material", list(materials.keys()), index=0)
        layer_height = st.number_input("Layer Height (mm)", 0.05, 1.0, 0.3, step=0.05)
        initial_layer_height = st.number_input("Initial Layer Height (mm)", 0.05, 1.0, 0.3)
        line_width = st.number_input("Line Width (mm)", 0.2, 1.0, 0.4)
        wall_thickness = st.number_input("Wall Thickness (mm)", 0.4, 5.0, 1.2)
        wall_count = st.number_input("Wall Line Count", 1, 10, 3)

    with col2:
        infill_density = st.slider("Infill Density (%)", 0, 100, 20)
        infill_pattern = st.selectbox("Infill Pattern", infill_patterns, index=0)
        infill_overlap = st.number_input("Infill Overlap (%)", 0, 100, 10)
        top_bottom_thickness = st.number_input("Top/Bottom Thickness (mm)", 0.4, 5.0, 0.8)
        top_layers = st.number_input("Top Layers", 1, 10, 3)
        bottom_layers = st.number_input("Bottom Layers", 1, 10, 3)

    with col3:
        print_speed = st.number_input("Print Speed (mm/s)", 10, 300, 200)
        travel_speed = st.number_input("Travel Speed (mm/s)", 10, 300, 125)
        enable_retraction = st.checkbox("Enable Retraction", value=True)
        support = st.checkbox("Generate Support", value=False)
        adhesion_type = st.selectbox("Build Plate Adhesion", ["None", "Brim", "Raft", "Skirt"], index=1)

    params = {
        "material_density": materials[material],
        "infill_density": infill_density,
        "wall_thickness": wall_thickness,
        "top_bottom_thickness": top_bottom_thickness,
        "layer_height": layer_height,
        "support": support,
    }

    if st.button("📊 Estimate Print Weight"):
        if uploaded_file is None:
            st.warning("Please upload an STL file first.")
        else:
            weight = calculate_weight(uploaded_file, params)
            if weight:
                st.markdown("### 🧱 Estimated Print Weight")
                st.subheader(f"Approximate Weight: **{weight} g**")

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("Made with ❤️ for 3D printing enthusiasts | Approximation model (no slicer).")
