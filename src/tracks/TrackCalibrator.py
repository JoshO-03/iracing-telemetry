import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.widgets import Slider
import json
from scipy.optimize import least_squares
from scipy import ndimage
import sys
import os

from analysis.cornerDetection import detectCorners


# ======================
# CONFIG
# ======================

# Default values
CSV_FILE = "data/telemetry.csv"
IMAGE_FILE = "tracks/models/okayama/okayama.png"
OUTPUT_FILE = "tracks/models/okayama/okayama_calibration.json"
LAP = 3

# Parse command-line arguments
# Usage: python3 TrackCalibrator.py [csv_file] [calibration_file] [lap] [image_file]
if len(sys.argv) > 1:
    CSV_FILE = sys.argv[1]
if len(sys.argv) > 2:
    OUTPUT_FILE = sys.argv[2]
if len(sys.argv) > 3:
    LAP = int(sys.argv[3])
if len(sys.argv) > 4:
    IMAGE_FILE = sys.argv[4]
else:
    # Try to read IMAGE_FILE from calibration JSON if it exists
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            cal_data = json.load(f)
            IMAGE_FILE = cal_data.get('image_file', IMAGE_FILE)

print(f"\n{'='*50}")
print("TRACK CALIBRATION TOOL")
print(f"{'='*50}")
print(f"CSV File: {CSV_FILE}")
print(f"Calibration: {OUTPUT_FILE}")
print(f"Image File: {IMAGE_FILE}")
print(f"Lap: {LAP}")
print(f"{'='*50}\n")


# ======================
# LOAD DATA
# ======================

df = pd.read_csv(CSV_FILE)
df = df[df["Lap"] == LAP]

lat = df["Lat"].values
lon = df["Lon"].values

# GPS -> metres
lat_scale = 111320
lon_scale = 111320 * np.cos(np.mean(lat) * np.pi / 180)

x = (lon - np.mean(lon)) * lon_scale
y = (lat - np.mean(lat)) * lat_scale

image = mpimg.imread(IMAGE_FILE)


# ======================
# CALIBRATOR CLASS
# ======================

class TrackCalibrator:
    def __init__(self, x, y, image, telemetry_points=None, image_points=None):
        self.x = x
        self.y = y
        self.image = image
        self.rotation_angle = 0  # Track rotation in degrees
        self.telemetry_points = telemetry_points if telemetry_points is not None else []
        self.image_points = image_points if image_points is not None else []
        self.point_counter = len(self.telemetry_points)
        
        self.fig, (self.ax_telem, self.ax_img) = plt.subplots(
            1, 2, figsize=(16, 7)
        )
        
        # Setup telemetry plot
        self.ax_telem.plot(x, y, color="lightgray", linewidth=1, label="Racing line")
        self.ax_telem.set_aspect('equal')
        self.ax_telem.set_title("Racing Line - Click points", fontsize=12, fontweight='bold')
        self.ax_telem.grid(True, alpha=0.3)
        self.telem_scatter = self.ax_telem.scatter([], [], c='red', s=20, zorder=5)
        self.telem_text_list = []
        
        # Add existing telemetry points if any
        for i, (px, py) in enumerate(self.telemetry_points):
            self.add_label_to_telem(px, py, i + 1)
        
        # Setup image plot
        self.img_display = self.ax_img.imshow(image)
        self.ax_img.set_title("Track Map - Click matching points\n(Use +/- keys to rotate)", fontsize=12, fontweight='bold')
        self.img_scatter = self.ax_img.scatter([], [], c='red', s=20, zorder=5)
        self.img_text_list = []
        
        # Add existing image points if any
        for i, (px, py) in enumerate(self.image_points):
            self.add_label_to_img(px, py, i + 1)
        
        # Connect events
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Instructions
        self.fig.text(
            0.5, 0.02,
            "Instructions: Click matching points on both sides. Scroll to zoom. "
            "Right-click to undo last point. Close window when done (min 3 points).",
            ha='center', fontsize=10, style='italic'
        )
        
        # Current target info
        self.info_text = self.fig.text(
            0.5, 0.98,
            self.get_info_text(),
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        
        # Store zoom levels
        self.ax_telem.xmin, self.ax_telem.xmax = self.ax_telem.get_xlim()
        self.ax_telem.ymin, self.ax_telem.ymax = self.ax_telem.get_ylim()
        self.ax_img.xmin, self.ax_img.xmax = self.ax_img.get_xlim()
        self.ax_img.ymin, self.ax_img.ymax = self.ax_img.get_ylim()
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        plt.show()
    
    def get_info_text(self):
        which_side = "RACING LINE" if len(self.telemetry_points) == len(self.image_points) else "TRACK MAP"
        return f"Point #{self.point_counter + 1} | Rotation: {self.rotation_angle}° | Waiting for click on {which_side}"
    
    def on_click(self, event):
        if event.inaxes is None:
            return
        
        if event.button == 3:  # Right click to undo
            self.undo_last_point()
            return
        
        if event.button != 1:  # Only left click
            return
        
        # Determine which axis should accept clicks
        # Click on racing line first (when equal), then on track map
        expecting_telem = len(self.telemetry_points) == len(self.image_points)
        expecting_img = len(self.telemetry_points) > len(self.image_points)
        
        x_click, y_click = event.xdata, event.ydata
        
        # Check if clicking on correct subplot
        if expecting_telem and event.inaxes == self.ax_telem:
            self.telemetry_points.append([x_click, y_click])
            self.add_label_to_telem(x_click, y_click, self.point_counter + 1)
            self.update_scatter()
            self.info_text.set_text(self.get_info_text())
            self.fig.canvas.draw_idle()
            
        elif expecting_img and event.inaxes == self.ax_img:
            self.image_points.append([x_click, y_click])
            self.add_label_to_img(x_click, y_click, self.point_counter + 1)
            self.point_counter += 1
            self.update_scatter()
            self.info_text.set_text(self.get_info_text())
            self.fig.canvas.draw_idle()
    
    def add_label_to_telem(self, x, y, label):
        text = self.ax_telem.text(
            x, y, str(label),
            fontsize=8, fontweight='bold', color='red',
            ha='center', va='center',
            bbox=dict(boxstyle='circle', facecolor='white', edgecolor='red', linewidth=1.5)
        )
        self.telem_text_list.append(text)
    
    def add_label_to_img(self, x, y, label):
        text = self.ax_img.text(
            x, y, str(label),
            fontsize=8, fontweight='bold', color='red',
            ha='center', va='center',
            bbox=dict(boxstyle='circle', facecolor='white', edgecolor='red', linewidth=1.5)
        )
        self.img_text_list.append(text)
    
    def update_scatter(self):
        if self.telemetry_points:
            telem_arr = np.array(self.telemetry_points)
            self.telem_scatter.set_offsets(telem_arr)
        
        if self.image_points:
            img_arr = np.array(self.image_points)
            self.img_scatter.set_offsets(img_arr)
    
    def undo_last_point(self):
        if len(self.telemetry_points) > len(self.image_points):
            self.telemetry_points.pop()
            if self.telem_text_list:
                self.telem_text_list.pop().remove()
        elif len(self.image_points) > len(self.telemetry_points):
            self.image_points.pop()
            if self.img_text_list:
                self.img_text_list.pop().remove()
            self.point_counter -= 1
        
        self.update_scatter()
        self.info_text.set_text(self.get_info_text())
        self.fig.canvas.draw_idle()
    
    def on_scroll(self, event):
        if event.inaxes == self.ax_telem:
            self.zoom_axis(self.ax_telem, event)
        elif event.inaxes == self.ax_img:
            self.zoom_axis(self.ax_img, event)
    
    def zoom_axis(self, ax, event):
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        xdata = event.xdata
        ydata = event.ydata
        
        if event.button == 'up':
            scale_factor = 0.8
        elif event.button == 'down':
            scale_factor = 1.2
        else:
            return
        
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        
        self.fig.canvas.draw_idle()
    
    def on_key_press(self, event):
        """Handle keyboard shortcuts for rotation"""
        if event.key == 'plus' or event.key == '=':
            self.rotation_angle = (self.rotation_angle + 5) % 360
            self.update_image_rotation()
        elif event.key == 'minus' or event.key == '_':
            self.rotation_angle = (self.rotation_angle - 5) % 360
            self.update_image_rotation()
    
    def update_image_rotation(self):
        """Rotate the track map image with padding to prevent clipping"""
        # Pad image to prevent clipping when rotated
        h, w = self.image.shape[:2]
        # Calculate padding needed for full rotation
        padding = int(np.sqrt(h**2 + w**2))
        padded = np.pad(self.image, ((padding, padding), (padding, padding), (0, 0)), mode='constant', constant_values=0)
        
        # Rotate with reshape=False to maintain size
        rotated = ndimage.rotate(padded, self.rotation_angle, reshape=False)
        self.img_display.set_data(rotated)
        self.info_text.set_text(self.get_info_text())
        self.fig.canvas.draw_idle()
    
    def get_points(self):
        return np.array(self.telemetry_points), np.array(self.image_points)


# ======================
# RUN CALIBRATOR
# ======================



# Load existing calibration if provided
existing_telem_points = None
existing_image_points = None

if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, 'r') as f:
        cal_data = json.load(f)
    existing_telem_points = cal_data.get('telemetry_points', [])
    existing_image_points = cal_data.get('image_points', [])
    print(f"✓ Loaded existing calibration from: {OUTPUT_FILE}")
    print(f"  - Existing points: {len(existing_telem_points)}")
    # Update IMAGE_FILE from calibration if not explicitly provided
    if len(sys.argv) <= 4:
        IMAGE_FILE = cal_data.get('image_file', IMAGE_FILE)

print("\nInstructions:")
print("  1. Click matching points on RACING LINE first")
print("  2. Then click the same point on TRACK MAP")
print("  3. Repeat for at least 3 points (4+ recommended)")
print("  4. Right-click to undo last point")
print("  5. Scroll to zoom in/out")
print("  6. Use + and - keys to rotate the track map")
print("  7. Close the window when finished\n")

calibrator = TrackCalibrator(x, y, image, existing_telem_points, existing_image_points)
telemetry_clicks, image_clicks = calibrator.get_points()

if len(telemetry_clicks) < 3:
    print("\n❌ Error: Need at least 3 points. Got", len(telemetry_clicks))
    exit(1)

# Calculate how many new points were added
new_points_count = len(telemetry_clicks) - (len(existing_telem_points) if existing_telem_points else 0)


# ======================
# AFFINE SOLVER
# ======================

def affine_matrix(points1, points2):
    A = []
    B = []
    
    for (px, py), (ux, uy) in zip(points1, points2):
        A.append([px, py, 1, 0, 0, 0])
        A.append([0, 0, 0, px, py, 1])
        B.append(ux)
        B.append(uy)
    
    A = np.array(A)
    B = np.array(B)
    
    result, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
    return result


matrix = affine_matrix(telemetry_clicks, image_clicks)

print("\n✓ Calibration matrix computed:")
print(matrix)


# ======================
# SECTOR DATA COLLECTION
# ======================

def collect_sector_data():
    """Collect lap distance and sector information from user"""
    print("\n" + "="*50)
    print("SECTOR CONFIGURATION")
    print("="*50)
    
    try:
        lap_distance = float(input("\nEnter total lap distance (metres): "))
        if lap_distance <= 0:
            print("Invalid lap distance. Skipping sector data.")
            return None
        
        num_sectors = int(input("Enter number of sectors: "))
        if num_sectors <= 0:
            print("Invalid number of sectors. Skipping sector data.")
            return None
        
        sectors = []
        sector_start = 0
        
        for i in range(1, num_sectors + 1):
            sector_end = float(input(f"Enter sector {i} end distance (metres): "))
            
            if sector_end <= sector_start or sector_end > lap_distance:
                print(f"Invalid sector end distance. Must be > {sector_start} and <= {lap_distance}")
                return None
            
            # Calculate sector boundary percentage: (end_distance / total_distance) × 100
            end_percentage = (sector_end / lap_distance) * 100
            start_percentage = (sector_start / lap_distance) * 100
            
            sectors.append({
                "sector": i,
                "startDistPct": round(start_percentage, 2),
                "endDistPct": round(end_percentage, 2)
            })
            
            sector_start = sector_end
        
        print("\n✓ Sector data collected:")
        for sector in sectors:
            print(f"  Sector {sector['sector']}: {sector['startDistPct']}% - {sector['endDistPct']}%")
        
        return sectors
    
    except ValueError:
        print("Invalid input. Skipping sector data.")
        return None


sector_data = collect_sector_data()


# ======================
# SAVE
# ======================

calibration = {
    "matrix": matrix.tolist(),
    "image_file": IMAGE_FILE,
    "telemetry_points": telemetry_clicks.tolist(),
    "image_points": image_clicks.tolist(),
    "corners": detectCorners(df, LAP),
}

# Add sector data if collected
if sector_data:
    calibration["sectors"] = sector_data

with open(OUTPUT_FILE, "w") as f:
    json.dump(calibration, f, indent=4)

print(f"\n✓ Calibration saved to: {OUTPUT_FILE}")
print(f"  - Total points: {len(telemetry_clicks)}")
if existing_telem_points:
    print(f"  - Existing points: {len(existing_telem_points)}")
    print(f"  - New points added: {new_points_count}")
print("="*50 + "\n")