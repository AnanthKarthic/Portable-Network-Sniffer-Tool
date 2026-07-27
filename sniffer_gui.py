import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict, Counter
from mac_vendor_lookup import MacLookup

SCAN_DURATION = 10  # seconds
INTERFACE = "wlan0"  

class PacketSnifferGUI:
    def __init__(self, root):
        tk.Label(root, text="Built by Ananth Karthic", font=("Fira Code", 10), fg="gray", anchor="center", justify="center").pack(pady=(5, 0))

        self.root = root
        self.root.title("Network Sniffer & Device Tracker")

        self.label = tk.Label(root, text="Status: Waiting to start...", font=("Fira Code", 11))
        self.label.pack(pady=10)

        self.timer_label = tk.Label(root, text="Time left: --", font=("Fira Code", 11))
        self.timer_label.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.start_button = tk.Button(root, text="Start Scan", command=self.start_scan)
        self.start_button.pack(pady=10)

        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack()

        self.mac_lookup = MacLookup()

    def start_scan(self):
        self.start_button.config(state=tk.DISABLED)
        self.label.config(text="Scanning devices with arp-scan...")
        self.progress["value"] = 0
        self.ax.clear()
        self.canvas.draw()

        self.device_counts = defaultdict(int)

        threading.Thread(target=self.run_scan).start()
        threading.Thread(target=self.update_timer).start()

    def run_scan(self):
        try:
            output = subprocess.check_output(
                ["sudo", "arp-scan", "--interface", INTERFACE, "--localnet"],
                timeout=SCAN_DURATION,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            )
            for line in output.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    mac = parts[1].strip()
                    self.device_counts[mac] += 1
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print("Error:", e)

        self.plot_data()

    def update_timer(self):
        for i in range(SCAN_DURATION):
            self.timer_label.config(text=f"Time left: {SCAN_DURATION - i}s")
            self.progress["value"] = int((i + 1) / SCAN_DURATION * 100)
            time.sleep(1)
        self.label.config(text="Processing complete.")

    def plot_data(self):
        if not self.device_counts:
            self.ax.text(0.5, 0.5, 'No devices detected', ha='center', va='center', fontsize=14)
        else:
            vendor_counts = Counter()
            for mac, count in self.device_counts.items():
                try:
                    vendor = self.mac_lookup.lookup(mac)
                except:
                    vendor = "Unknown"
                vendor_counts[vendor] += count

            sorted_vendors = vendor_counts.most_common()
            vendors = [v for v, _ in sorted_vendors]
            counts = [c for _, c in sorted_vendors]

            self.ax.clear()
            self.ax.barh(vendors, counts, color='skyblue')
            self.ax.set_xlabel('Number of Devices')
            self.ax.set_title('Devices Detected by Manufacturer')
            self.ax.invert_yaxis()  # highest on top

        self.figure.tight_layout()  # <-- Here it is
        self.canvas.draw()
        self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = PacketSnifferGUI(root)
    root.mainloop()
