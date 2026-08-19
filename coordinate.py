import pyautogui
import tkinter as tk
import time

# Get screen information
root = tk.Tk()
root.withdraw()

print("Tkinter screen size :", root.winfo_screenwidth(), root.winfo_screenheight())
print("PyAutoGUI screen size:", pyautogui.size())

print("\nMove mouse to the TOP-LEFT corner of your screen.")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        x, y = pyautogui.position()
        print(f"Mouse: X={x}, Y={y}        ", end="\r", flush=True)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")

root.destroy()