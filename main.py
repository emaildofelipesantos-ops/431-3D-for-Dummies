import streamlit as st
import trimesh
import io
import zipfile
import subprocess
import os
import time

# BANCO DE DADOS COMPLETO POR FABRICANTE
DATABASE = {
    "Creality": {
        "Ender 3 V3 KE": {"x": 220, "y": 220, "z": 240},
        "Ender 3 (V2/Neo/S1)": {"x": 220, "y": 220, "z": 250},
        "Ender 3 Max Neo": {"x": 300, "y": 300, "z": 340},
        "Ender 5 S1": {"x": 220, "y": 220, "z": 280},
        "Ender 6": {"x": 250, "y": 250, "z": 400},
        "K1 / K1C": {"x": 220, "y": 220, "z": 250},
        "K1 Max": {"x": 300, "y": 300, "z": 300},
        "CR-10 Smart Pro": {"x": 300, "y": 300, "z": 400},
        "CR-M4": {"x": 450, "y": 450, "z": 470}
    },
    "Bambu Lab": {
        "A1 Mini": {"x": 180, "y": 180, "z": 180},
        "A1": {"x": 256, "y": 256, "z": 256},
        "P1P / P1S": {"x": 256, "y": 256, "z": 256},
        "X1 Carbon / X1E": {"x": 256, "y": 256, "z": 256}
    },
    "Prusa": {
        "Mini+": {"x": 180, "y": 180, "z": 180},
        "MK3S+ / MK4": {"x": 250, "y": 210, "z": 210},
        "XL (Single/Five Head)": {"x": 360, "y": 360, "z": 360}
    },
    "Anycubic": {
        "Kobra 2 Neo/Pro": {"x": 220, "y": 220, "z": 250},
        "Kobra 2 Plus": {"x": 320, "y": 320, "z": 400},
        "Kobra 2 Max": {"x": 420, "y": 420, "z": 500},
        "Photon Mono M5s (Resin)": {"x": 218, "y": 123, "z": 200}
    },
    "Elegoo": {
        "Neptune 4 / 4 Pro": {"x": 225, "y": 225, "z": 265},
        "Neptune 4 Plus": {"x": 320, "y": 320, "z": 385},
        "Neptune 4 Max": {"x": 420, "y": 420, "z": 480}
    },
    "Artillery": {
        "Sidewinder X2 / X4": {"x": 300, "y": 300, "z": 400},
        "Genius Pro": {"x": 220, "y": 220, "z": 250}
    }
}

st.set_page_config(page_title="431 3D for Dummies", page_icon="🧩", layout
