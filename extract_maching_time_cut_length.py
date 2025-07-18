import json

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# Load the data
with open("data/laser_cut_inventory.json", "r", encoding="utf-8") as file:
    data = json.load(file)

L = []
P = []
T = []

for part in data["laser_cut_parts"]:
    L.append(part["cutting_length"])
    P.append(part["piercing_points"])
    T.append(part["machine_time"])

L = np.array(L)
P = np.array(P)
T = np.array(T)

# Build the polynomial feature matrix manually (degree 3)
X = np.column_stack([L**3, L**2 * P, L * P**2, P**3, L**2, L * P, P**2, L, P, np.ones_like(L)])

# Solve for coefficients using least squares
coeffs, *_ = np.linalg.lstsq(X, T, rcond=None)

# Generate 3D grid for plotting
L_grid, P_grid = np.meshgrid(np.linspace(min(L), max(L), 50), np.linspace(min(P), max(P), 50))

# Flatten and create feature matrix for the grid
L_flat = L_grid.ravel()
P_flat = P_grid.ravel()
X_grid = np.column_stack([L_flat**3, L_flat**2 * P_flat, L_flat * P_flat**2, P_flat**3, L_flat**2, L_flat * P_flat, P_flat**2, L_flat, P_flat, np.ones_like(L_flat)])

# Predict T values over the grid
T_grid = X_grid @ coeffs
T_grid = T_grid.reshape(L_grid.shape)

# Plot
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Plot data points
ax.scatter(L, P, T, alpha=0.5, color="blue", label="Data Points")

# Plot surface
ax.plot_surface(L_grid, P_grid, T_grid, cmap="plasma", alpha=0.6, edgecolor="none")

# Axes labels
ax.set_title("Degree 3 Polynomial Fit: T(L, P)")
ax.set_xlabel("Cutting Length (inches)")
ax.set_ylabel("Piercing Points")
ax.set_zlabel("Machine Time (seconds)")
ax.view_init(elev=25, azim=135)
plt.tight_layout()
plt.legend()
plt.show()

terms = ["L^3", "L^2·P", "L·P^2", "P^3", "L^2", "L·P", "P^2", "L", "P", "1"]

# Build and print the function
equation = " + ".join(f"{coef:.5f}·{term}" for coef, term in zip(coeffs, terms))
print("Machine Time function:\nT(L, P) =", equation)


def piercing_time(L_val: float, P_val: float) -> float:
    """
    Estimate piercing-only time (seconds) for a given
    cutting length L and piercing-point count P,
    using the fitted degree-3 polynomial coefficients.
    """
    return (
        coeffs[1] * L_val**2 * P_val  #  L²·P
        + coeffs[2] * L_val * P_val**2  #  L·P²
        + coeffs[3] * P_val**3  #  P³
        + coeffs[5] * L_val * P_val  #  L·P
        + coeffs[6] * P_val**2  #  P²
        + coeffs[8] * P_val  #  P
    )


# Build a readable equation string for piercing terms
pierce_terms = [
    ("L^2·P", coeffs[1]),
    ("L·P^2", coeffs[2]),
    ("P^3", coeffs[3]),
    ("L·P", coeffs[5]),
    ("P^2", coeffs[6]),
    ("P", coeffs[8]),
]
pierce_eq = " + ".join(f"{c:.5f}·{t}" for t, c in pierce_terms if abs(c) > 1e-12)

print("Piercing-time function:")
print(f"Tp(L, P) = {pierce_eq}")

# --- quick test ----------------------------------------------------------
L_demo, P_demo = 100.0, 10
print(f"\nPiercing-time estimate for L={L_demo}, P={P_demo}: {piercing_time(L_demo, P_demo):.3f} s")
