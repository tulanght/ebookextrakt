import customtkinter as ctk
from PIL import Image, ImageOps
import sys

ctk.set_appearance_mode("Dark")

root = ctk.CTk()
root.geometry("400x400")

# Test with a dummy image (create a solid red rectangle 50x200 to test padding)
img = Image.new('RGB', (50, 200), color='red')

# The fix applied in library_view.py
img.thumbnail((120, 160))
img_padded = ImageOps.pad(img, (120, 160), color="#1E293B") 

ctk_img = ctk.CTkImage(light_image=img_padded, dark_image=img_padded, size=(120, 160))

lbl = ctk.CTkLabel(root, text="", image=ctk_img, bg_color="green")
lbl.pack(pady=50)

print("Test window opened. The red block should be centered in a 120x160 dark box.")

# Close after 3 seconds
root.after(3000, root.destroy)
root.mainloop()
