import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import customtkinter as ctk

# --- Styling constants ---
BG_COLOR = "#23272e"
CARD_COLOR = "#232b36"
ACCENT_COLOR = "#4fc3f7"
BUTTON_ACCENT = "#1de9b6"
TITLE_FONT = ("Segoe UI", 28, "bold")
LABEL_FONT = ("Segoe UI", 15, "bold")
BUTTON_FONT = ("Segoe UI", 15, "bold")
TOOLTIP_FONT = ("Segoe UI", 11)
CANVAS_W, CANVAS_H = 520, 390
FRAME_PAD = 24
CARD_RADIUS = 20

# --- Filter definitions (name, emoji/icon, tooltip) ---
FILTERS = [
    ("Modern Sepia", "🟤", "Warm, modern sepia"),
    ("Cinematic", "🎬", "Cinematic teal & orange"),
    ("Teal & Orange", "🌅", "Blockbuster color grade"),
    ("Soft Pastel", "🌸", "Pastel, soft look"),
    ("Deep Blue", "🌊", "Cool, deep blue tint"),
    ("Retro Fade", "📼", "Retro faded film"),
    ("Vibrant Pop", "🌈", "High vibrance & pop"),
    ("Black & White", "⚫️", "Classic B&W"),
    ("Dream Glow", "✨", "Soft dreamy glow"),
    ("Clean Sharpen", "🔪", "Crisp, clean sharpen"),
    ("Matte Film", "🎞️", "Matte, flat film look"),
    ("Golden Hour", "🌇", "Warm golden hour tint"),
    ("Cyberpunk", "🦾", "Vivid magenta/cyan pop"),
    ("Sunset", "🌅", "Sunset orange/pink"),
    ("Frosted", "❄️", "Cool, frosted look"),
    ("Noir", "🎩", "High-contrast noir B&W"),
]

# Map filter names to functions for concise logic
FILTER_FUNCTIONS = {
    "Modern Sepia": lambda self, img, inten: self._modern_sepia(img, inten),
    "Cinematic": lambda self, img, inten: self._cinematic(img, inten),
    "Teal & Orange": lambda self, img, inten: self._teal_orange(img, inten),
    "Soft Pastel": lambda self, img, inten: self._soft_pastel(img, inten),
    "Deep Blue": lambda self, img, inten: self._deep_blue(img, inten),
    "Retro Fade": lambda self, img, inten: self._retro_fade(img, inten),
    "Vibrant Pop": lambda self, img, inten: self._vibrant_pop(img, inten),
    "Black & White": lambda self, img, inten: self._black_white(img, inten),
    "Dream Glow": lambda self, img, inten: self._dream_glow(img, inten),
    "Clean Sharpen": lambda self, img, inten: self._clean_sharpen(img, inten),
    "Matte Film": lambda self, img, inten: self._matte_film(img, inten),
    "Golden Hour": lambda self, img, inten: self._golden_hour(img, inten),
    "Cyberpunk": lambda self, img, inten: self._cyberpunk(img, inten),
    "Sunset": lambda self, img, inten: self._sunset(img, inten),
    "Frosted": lambda self, img, inten: self._frosted(img, inten),
    "Noir": lambda self, img, inten: self._noir(img, inten),
}

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0,0,0,0)
        x = x + self.widget.winfo_rootx() + 30
        y = y + self.widget.winfo_rooty() + cy + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#333", fg="white", relief=tk.SOLID, borderwidth=1,
                         font=TOOLTIP_FONT, padx=8, pady=4)
        label.pack(ipadx=1)
    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class ImageProcessingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processing GUI")
        self.root.configure(bg=BG_COLOR)
        self.root.state('zoomed')  # Fullscreen
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.input_image = None
        self.output_image = None
        self.strength = 50
        self.exposure = 1.0
        self.contrast = 1.0
        self.selected_filter = FILTERS[0][0]
        self._build_ui()

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self._create_title()
        self._create_image_area()
        self._create_controls_panel()

    def _create_title(self):
        self.title_label = ctk.CTkLabel(
            self.root,
            text="Image Processing GUI",
            font=TITLE_FONT,
            text_color=ACCENT_COLOR,
            bg_color=BG_COLOR
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(FRAME_PAD, 8), sticky="nwe")

    def _create_image_area(self):
        frame = ctk.CTkFrame(self.root, fg_color=CARD_COLOR, corner_radius=CARD_RADIUS)
        frame.grid(row=1, column=0, padx=(FRAME_PAD, 12), pady=(0, FRAME_PAD), sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        # Input
        self.input_canvas = tk.Canvas(
            frame, width=CANVAS_W, height=CANVAS_H, bg="#181a20", bd=0, highlightthickness=0, relief='ridge'
        )
        self.input_canvas.grid(row=0, column=0, padx=24, pady=16, sticky="nsew")
        ctk.CTkLabel(frame, text="Input Image", font=LABEL_FONT, text_color="white", bg_color=CARD_COLOR).grid(row=1, column=0, pady=(0, 12))
        # Output
        self.output_canvas = tk.Canvas(
            frame, width=CANVAS_W, height=CANVAS_H, bg="#181a20", bd=0, highlightthickness=0, relief='ridge'
        )
        self.output_canvas.grid(row=0, column=1, padx=24, pady=16, sticky="nsew")
        ctk.CTkLabel(frame, text="Output Image", font=LABEL_FONT, text_color="white", bg_color=CARD_COLOR).grid(row=1, column=1, pady=(0, 12))

    def _create_controls_panel(self):
        panel = ctk.CTkFrame(self.root, fg_color=CARD_COLOR, corner_radius=CARD_RADIUS)
        panel.grid(row=1, column=1, padx=(0, FRAME_PAD), pady=(0, FRAME_PAD), sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        # Filter selection
        ctk.CTkLabel(panel, text="Filters", font=LABEL_FONT, text_color=ACCENT_COLOR, bg_color=CARD_COLOR).grid(row=0, column=0, pady=(18, 8), sticky="w")
        self.filter_buttons = {}
        filter_frame = ctk.CTkFrame(panel, fg_color="transparent")
        filter_frame.grid(row=1, column=0, pady=(0, 18), sticky="ew")
        max_per_row = 5
        for idx, (name, icon, tip) in enumerate(FILTERS):
            row, col = divmod(idx, max_per_row)
            btn = ctk.CTkButton(
                filter_frame, text=f"{icon}\n{name}", font=("Segoe UI", 13, "bold"), width=90, height=54,
                fg_color=ACCENT_COLOR if name == self.selected_filter else "#333", text_color="white",
                hover_color=BUTTON_ACCENT, corner_radius=10, command=lambda n=name: self._select_filter(n)
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            Tooltip(btn, tip)
            self.filter_buttons[name] = btn
        for c in range(max_per_row):
            filter_frame.grid_columnconfigure(c, weight=1)
        # Centered Effect Intensity slider
        slider_frame = ctk.CTkFrame(panel, fg_color="transparent")
        slider_frame.grid(row=2, column=0, columnspan=2, pady=(8, 0), sticky="ew")
        slider_frame.grid_columnconfigure(0, weight=1)
        slider_frame.grid_columnconfigure(1, weight=0)
        slider_frame.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(slider_frame, text="-20", font=LABEL_FONT, text_color="#aaa", bg_color="transparent").grid(row=0, column=0, sticky="e", padx=(0, 8))
        self.intensity_slider = ctk.CTkSlider(
            slider_frame, from_=-20, to=20, number_of_steps=40, command=self._on_intensity_change,
            button_color=ACCENT_COLOR, button_hover_color=BUTTON_ACCENT, progress_color=ACCENT_COLOR, height=18
        )
        self.intensity_slider.set(0)
        self.intensity_slider.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(slider_frame, text="+20", font=LABEL_FONT, text_color="#aaa", bg_color="transparent").grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.intensity_value = ctk.CTkLabel(
            slider_frame, text="0", width=36, height=28, corner_radius=6, fg_color="#23272e", font=BUTTON_FONT
        )
        self.intensity_value.grid(row=0, column=3, padx=(12, 0))
        Tooltip(self.intensity_slider, "Adjust the effect intensity (left: reverse, right: strong)")
        # Contrast
        ctk.CTkLabel(panel, text="Contrast", font=LABEL_FONT, text_color="white", bg_color=CARD_COLOR).grid(row=3, column=0, padx=8, pady=(8, 0), sticky="w")
        self.contrast_slider = ctk.CTkSlider(
            panel, from_=0.5, to=2.0, number_of_steps=30, command=self._on_contrast_change,
            button_color=ACCENT_COLOR, button_hover_color=BUTTON_ACCENT, progress_color=ACCENT_COLOR, height=18
        )
        self.contrast_slider.set(self.contrast)
        self.contrast_slider.grid(row=4, column=0, padx=8, pady=(0, 8), sticky="ew")
        self.contrast_value = ctk.CTkLabel(
            panel, text=f"{self.contrast:.2f}", width=36, height=28, corner_radius=6, fg_color="#23272e", font=BUTTON_FONT
        )
        self.contrast_value.grid(row=4, column=1, padx=(0, 8), pady=(0, 8))
        Tooltip(self.contrast_slider, "Adjust image contrast")
        # Exposure
        ctk.CTkLabel(panel, text="Exposure", font=LABEL_FONT, text_color="white", bg_color=CARD_COLOR).grid(row=5, column=0, padx=8, pady=(8, 0), sticky="w")
        self.exposure_slider = ctk.CTkSlider(
            panel, from_=0.1, to=3.0, number_of_steps=29, command=self._on_exposure_change,
            button_color=ACCENT_COLOR, button_hover_color=BUTTON_ACCENT, progress_color=ACCENT_COLOR, height=18
        )
        self.exposure_slider.set(self.exposure)
        self.exposure_slider.grid(row=6, column=0, padx=8, pady=(0, 8), sticky="ew")
        self.exposure_value = ctk.CTkLabel(
            panel, text=f"{self.exposure:.2f}", width=36, height=28, corner_radius=6, fg_color="#23272e", font=BUTTON_FONT
        )
        self.exposure_value.grid(row=6, column=1, padx=(0, 8), pady=(0, 8))
        Tooltip(self.exposure_slider, "Adjust image exposure")
        # Action buttons
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(18, 0), sticky="ew")
        btn_frame.grid_columnconfigure((0,1), weight=1)
        self.upload_btn = ctk.CTkButton(
            btn_frame, text="📤 Upload Image", command=self.upload_image, font=BUTTON_FONT, height=48, corner_radius=12,
            fg_color="#333", hover_color="#444", text_color="white", border_width=2, border_color=ACCENT_COLOR
        )
        self.upload_btn.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        Tooltip(self.upload_btn, "Upload an image from your computer")
        self.save_btn = ctk.CTkButton(
            btn_frame, text="💾 Save Image", command=self.save_image, font=BUTTON_FONT, height=48, corner_radius=12,
            fg_color=ACCENT_COLOR, hover_color=BUTTON_ACCENT, text_color="white"
        )
        self.save_btn.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        Tooltip(self.save_btn, "Save the processed image")

    def _select_filter(self, name):
        self.selected_filter = name
        for fname, btn in self.filter_buttons.items():
            btn.configure(fg_color=ACCENT_COLOR if fname == name else "#333")
        self.apply_filter()

    def _on_intensity_change(self, value):
        self.strength = int(float(value))
        self.intensity_value.configure(text=str(self.strength))
        self.apply_filter()

    def _on_contrast_change(self, value):
        self.contrast = float(value)
        self.contrast_value.configure(text=f"{self.contrast:.2f}")
        self.apply_filter()

    def _on_exposure_change(self, value):
        self.exposure = float(value)
        self.exposure_value.configure(text=f"{self.exposure:.2f}")
        self.apply_filter()

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if file_path:
            self.input_image = cv2.imread(file_path)
            input_rgb = cv2.cvtColor(self.input_image, cv2.COLOR_BGR2RGB)
            self.display_image(input_rgb, self.input_canvas)
            self.apply_filter()

    def save_image(self):
        if self.output_image is not None:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("TIFF files", "*.tiff"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                save_image = cv2.cvtColor(self.output_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(file_path, save_image)

    def apply_filter(self, *args):
        if self.input_image is None:
            return
        filter_type = self.selected_filter
        image_rgb = cv2.cvtColor(self.input_image, cv2.COLOR_BGR2RGB)
        intensity = self.strength / 20.0  # -1.0 to +1.0
        func = FILTER_FUNCTIONS.get(filter_type)
        out = func(self, image_rgb, intensity) if func else image_rgb
        # Apply contrast and exposure
        if self.contrast != 1.0:
            out = cv2.convertScaleAbs(out, alpha=self.contrast, beta=0)
        if self.exposure != 1.0:
            lab = cv2.cvtColor(out, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            l = cv2.convertScaleAbs(l, alpha=self.exposure)
            lab = cv2.merge((l, a, b))
            out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        self.output_image = out
        self.display_image(self.output_image, self.output_canvas)

    def _modern_sepia(self, image, intensity):
        # Warm sepia, negative reverses to cool
        kernel = np.array([[0.393, 0.769, 0.189],
                           [0.349, 0.686, 0.168],
                           [0.272, 0.534, 0.131]])
        sepia = cv2.transform(image, kernel)
        sepia = cv2.convertScaleAbs(sepia)
        if intensity >= 0:
            out = cv2.addWeighted(image, 1-abs(intensity), sepia, abs(intensity), 0)
        else:
            # Reverse: cool blue tone
            blue = image.copy()
            blue[...,0] = np.clip(blue[...,0]+60*abs(intensity), 0, 255)
            out = cv2.addWeighted(image, 1-abs(intensity), blue, abs(intensity), 0)
        return np.clip(out, 0, 255).astype(np.uint8)

    def _cinematic(self, image, intensity):
        # Teal & orange, with contrast
        if intensity == 0:
            return image
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] = np.clip(img[...,0] + 30*intensity, 0, 255)  # Blue
            img[...,2] = np.clip(img[...,2] + 30*intensity, 0, 255)  # Red
        else:
            img[...,1] = np.clip(img[...,1] + 30*(-intensity), 0, 255)  # Green
        img = cv2.convertScaleAbs(img, alpha=1+0.2*abs(intensity), beta=0)
        return img

    def _teal_orange(self, image, intensity):
        # Blockbuster look
        if intensity == 0:
            return image
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] = np.clip(img[...,0] + 40*intensity, 0, 255)
            img[...,2] = np.clip(img[...,2] + 40*intensity, 0, 255)
        else:
            img[...,1] = np.clip(img[...,1] + 40*(-intensity), 0, 255)
        img = cv2.convertScaleAbs(img, alpha=1+0.15*abs(intensity), beta=0)
        return img

    def _soft_pastel(self, image, intensity):
        # Pastel: brighten, reduce contrast, add blur
        if intensity == 0:
            return image
        img = cv2.convertScaleAbs(image, alpha=1-0.3*abs(intensity), beta=30*abs(intensity))
        if intensity > 0:
            img = cv2.GaussianBlur(img, (0,0), sigmaX=2*intensity)
        else:
            img = cv2.medianBlur(img, 3)
        return img

    def _deep_blue(self, image, intensity):
        # Deep blue/cool
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] = np.clip(img[...,0] + 60*intensity, 0, 255)
        else:
            img[...,2] = np.clip(img[...,2] + 60*(-intensity), 0, 255)
        return img.astype(np.uint8)

    def _retro_fade(self, image, intensity):
        # Faded retro: lower contrast, add magenta/green
        img = cv2.convertScaleAbs(image, alpha=1-0.4*abs(intensity), beta=20*abs(intensity))
        if intensity > 0:
            img[...,0] = np.clip(img[...,0] + 20*intensity, 0, 255)
            img[...,2] = np.clip(img[...,2] + 20*intensity, 0, 255)
        else:
            img[...,1] = np.clip(img[...,1] + 30*(-intensity), 0, 255)
        return img

    def _vibrant_pop(self, image, intensity):
        # High vibrance
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        if intensity > 0:
            hsv[...,1] = np.clip(hsv[...,1]*(1+0.8*intensity), 0, 255)
        else:
            hsv[...,1] = np.clip(hsv[...,1]*(1-0.8*(-intensity)), 0, 255)
        img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        return img

    def _black_white(self, image, intensity):
        # B&W, with fade or contrast
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        if intensity == 0:
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        if intensity > 0:
            img = cv2.convertScaleAbs(gray, alpha=1+0.8*intensity, beta=0)
        else:
            img = cv2.convertScaleAbs(gray, alpha=1-0.8*(-intensity), beta=30*(-intensity))
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    def _dream_glow(self, image, intensity):
        # Soft dreamy glow
        if intensity == 0:
            return image
        blur = cv2.GaussianBlur(image, (0,0), sigmaX=2+8*abs(intensity))
        if intensity > 0:
            out = cv2.addWeighted(image, 1-0.5*intensity, blur, 0.5*intensity, 0)
        else:
            out = cv2.addWeighted(image, 1+0.5*intensity, blur, -0.5*intensity, 0)
        return np.clip(out, 0, 255).astype(np.uint8)

    def _clean_sharpen(self, image, intensity):
        # Sharpen or soften
        if intensity == 0:
            return image
        if intensity > 0:
            kernel = np.array([[0, -1, 0], [-1, 5+2*intensity, -1], [0, -1, 0]])
            out = cv2.filter2D(image, -1, kernel)
        else:
            out = cv2.GaussianBlur(image, (0,0), sigmaX=2*(-intensity))
        return np.clip(out, 0, 255).astype(np.uint8)

    def _matte_film(self, image, intensity):
        # Matte: flatten contrast, slight fade
        img = cv2.convertScaleAbs(image, alpha=1-0.3*abs(intensity), beta=15*abs(intensity))
        lut = np.array([min(255, int(255*(i/255)**(1/(1+0.7*abs(intensity))))) for i in range(256)], dtype=np.uint8)
        img = cv2.LUT(img, lut)
        return img

    def _golden_hour(self, image, intensity):
        # Warm golden tint
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] -= 30*intensity
            img[...,1] += 20*intensity
            img[...,2] += 40*intensity
        else:
            img[...,0] += 20*(-intensity)
            img[...,2] -= 20*(-intensity)
        return np.clip(img, 0, 255).astype(np.uint8)

    def _cyberpunk(self, image, intensity):
        # Magenta/cyan pop
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] += 40*intensity
            img[...,2] += 60*intensity
        else:
            img[...,1] += 40*(-intensity)
            img[...,2] -= 40*(-intensity)
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)

    def _sunset(self, image, intensity):
        # Orange/pink sunset
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] += 20*intensity
            img[...,1] += 10*intensity
            img[...,2] += 40*intensity
        else:
            img[...,0] -= 20*(-intensity)
            img[...,2] -= 20*(-intensity)
        return np.clip(img, 0, 255).astype(np.uint8)

    def _frosted(self, image, intensity):
        # Cool, frosted look
        img = image.astype(np.float32)
        if intensity > 0:
            img[...,0] += 40*intensity
            img[...,1] += 20*intensity
            img = cv2.GaussianBlur(img, (0,0), sigmaX=2*intensity)
        else:
            img[...,2] += 40*(-intensity)
            img[...,1] -= 20*(-intensity)
        return np.clip(img, 0, 255).astype(np.uint8)

    def _noir(self, image, intensity):
        # High-contrast B&W
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        if intensity == 0:
            img = gray
        elif intensity > 0:
            img = cv2.convertScaleAbs(gray, alpha=1+2*intensity, beta=-40*intensity)
        else:
            img = cv2.convertScaleAbs(gray, alpha=1-1.5*(-intensity), beta=40*(-intensity))
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    def display_image(self, image, canvas):
        if image is None:
            return
        h, w = image.shape[:2]
        canvas_w, canvas_h = CANVAS_W, CANVAS_H
        image_aspect = w / h
        canvas_aspect = canvas_w / canvas_h
        if image_aspect > canvas_aspect:
            new_w = canvas_w
            new_h = int(canvas_w / image_aspect)
        else:
            new_h = canvas_h
            new_w = int(canvas_h * image_aspect)
        resized = cv2.resize(image, (new_w, new_h))
        img = Image.fromarray(resized)
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.delete("all")
        canvas.config(width=new_w, height=new_h)
        canvas.create_image(new_w/2, new_h/2, image=imgtk)
        canvas.image = imgtk

if __name__ == "__main__":
    root = ctk.CTk()
    app = ImageProcessingApp(root)
    root.mainloop()