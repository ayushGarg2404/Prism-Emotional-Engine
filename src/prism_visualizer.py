import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

def render_soul_map(vector, audit):
    # Setup the grid
    x = np.linspace(-3, 3, 60)
    y = np.linspace(-3, 3, 60)
    X, Y = np.meshgrid(x, y)
    
    # --- TOPOGRAPHIC ALGORITHM ---
    # Valence determines height (Peak vs Crater)
    # Agency determines "Surface Tension" (Smooth vs Chaotic)
    
    # Base shape (Gaussian Bell Curve)
    Z_base = vector.valence * 2 * np.exp(-(X**2 + Y**2)/2.0)
    
    # Chaos Factor (Low Agency = High Noise)
    chaos_level = (1.0 - vector.agency) * 0.3
    noise = np.random.normal(0, chaos_level, X.shape)
    
    # Final Terrain
    Z = Z_base + noise
    
    # --- VISUAL RENDERING ---
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Dynamic Coloring based on Masking
    if audit.detected_masking:
        cmap = 'ocean' # Cold/Deep colors for hidden emotions
        title_color = 'red'
        status = "MASKED / DISSONANT"
    else:
        cmap = 'magma' # Warm/Energy colors for authentic emotions
        title_color = 'black'
        status = "AUTHENTIC / RESONANT"

    surf = ax.plot_surface(X, Y, Z, cmap=cmap, edgecolor='none', alpha=0.9)
    
    # Aesthetics
    ax.set_zlim(-1, 2)
    ax.set_title(f"Prism Soul Map\nStatus: {status}", color=title_color, fontsize=14)
    ax.set_xlabel('Social Connection')
    ax.set_ylabel('Internal Clarity')
    ax.set_zlabel('Valence Amplitude')
    
    # Add a color bar
    fig.colorbar(surf, shrink=0.5, aspect=5)
    
    print("Displaying 3D Soul Map...")
    plt.show()