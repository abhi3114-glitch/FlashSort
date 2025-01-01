import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import threading
import time
import os

from .encoder import Encoder
from .decoder import Decoder

class FlashSortApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FlashSort - Offline Optical File Transfer")
        self.root.geometry("800x650")
        
        self.encoder = Encoder()
        self.decoder = Decoder()
        
        self.sender_images_iterator = None
        self.sender_running = False
        self.current_qr_image = None
        self.receiver_running = False
        self.received_file_ready = False
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.create_sender_tab()
        self.create_receiver_tab()

    def create_sender_tab(self):
        self.send_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.send_frame, text='Sender')
        
        # Controls
        ctrl_panel = ttk.Frame(self.send_frame)
        ctrl_panel.pack(fill='x', padx=10, pady=10)
        
        self.btn_select = ttk.Button(ctrl_panel, text="Select File", command=self.select_file)
        self.btn_select.pack(side='left', padx=5)
        
        self.lbl_file = ttk.Label(ctrl_panel, text="No file selected")
        self.lbl_file.pack(side='left', padx=5)
        
        self.lbl_fps = ttk.Label(ctrl_panel, text="FPS: 10")
        self.lbl_fps.pack(side='left', padx=20)
        
        self.fps_var = tk.IntVar(value=10)
        self.scale_fps = ttk.Scale(ctrl_panel, from_=1, to=30, variable=self.fps_var, orient='horizontal', command=lambda v: self.lbl_fps.config(text=f"FPS: {int(float(v))}"))
        self.scale_fps.pack(side='left', padx=5)
        
        self.btn_send = ttk.Button(ctrl_panel, text="Start Sending", command=self.toggle_sending, state='disabled')
        self.btn_send.pack(side='right', padx=5)
        
        # Canvas for QR
        self.qr_canvas = tk.Canvas(self.send_frame, bg='white')
        self.qr_canvas.pack(fill='both', expand=True, padx=20, pady=20)
        
    def create_receiver_tab(self):
        self.recv_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recv_frame, text='Receiver')
        
        # Controls
        ctrl_panel = ttk.Frame(self.recv_frame)
        ctrl_panel.pack(fill='x', padx=10, pady=10)
        
        self.btn_camera = ttk.Button(ctrl_panel, text="Start Camera", command=self.toggle_camera)
        self.btn_camera.pack(side='left', padx=5)
        
        self.btn_save = ttk.Button(ctrl_panel, text="Save Received File", command=self.save_file, state='disabled')
        self.btn_save.pack(side='right', padx=5)
        
        # Progress
        self.progress = ttk.Progressbar(self.recv_frame, orient='horizontal', length=100, mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
        self.lbl_status = ttk.Label(self.recv_frame, text="Ready to receive")
        self.lbl_status.pack(fill='x', padx=10)
        
        # Camera Feed
        self.cam_canvas = tk.Label(self.recv_frame, bg='black') # Using Label for video frames is standard in simple Tk/OpenCV apps
        self.cam_canvas.pack(fill='both', expand=True, padx=10, pady=10)

    # --- Sender Logic ---
    def select_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.lbl_file.config(text=os.path.basename(filename))
            count = self.encoder.load_file(filename)
            self.btn_send.config(state='normal', text=f"Start Sending ({count} chunks)")
            
    def toggle_sending(self):
        if self.sender_running:
            self.sender_running = False
            self.btn_send.config(text="Resume Sending")
            self.qr_canvas.delete("all")
        else:
            self.sender_running = True
            self.btn_send.config(text="Stop Sending")
            # If start fresh
            if not self.sender_images_iterator:
                self.sender_images_iterator = self.encoder.generate_frames()
            self.sender_loop()

    def sender_loop(self):
        if not self.sender_running:
            return
            
        try:
            pil_image = next(self.sender_images_iterator)
             # Resize to fit canvas if needed? QR codes are usually square.
            cw = self.qr_canvas.winfo_width()
            ch = self.qr_canvas.winfo_height()
            size = min(cw, ch) - 20
            if size > 10:
                pil_image = pil_image.resize((size, size), Image.Resampling.NEAREST)
            
            self.current_qr_image = ImageTk.PhotoImage(pil_image)
            self.qr_canvas.create_image(cw//2, ch//2, image=self.current_qr_image)
            
            # Calculate delay from FPS
            delay = int(1000 / self.fps_var.get())
            self.root.after(delay, self.sender_loop)
            
        except StopIteration:
            self.sender_running = False
            self.btn_send.config(text="Sending Complete (Restart)")
            self.sender_images_iterator = None # Reset
            messagebox.showinfo("Done", "All chunks displayed.")

    # --- Receiver Logic ---
    def toggle_camera(self):
        if self.receiver_running:
            self.receiver_running = False
            self.decoder.stop_camera()
            self.btn_camera.config(text="Start Camera")
        else:
            try:
                self.decoder.start_camera()
                self.receiver_running = True
                self.btn_camera.config(text="Stop Camera")
                self.receiver_loop()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def receiver_loop(self):
        if not self.receiver_running:
            return
            
        frame, progress = self.decoder.get_frame()
        if frame is not None:
            # Convert frame to Tkinter format
            # OpenCV BGR -> RGB
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_img)
            
            # Resize for display
            lw = self.cam_canvas.winfo_width()
            lh = self.cam_canvas.winfo_height()
            if lw > 10 and lh > 10:
                img.thumbnail((lw, lh))
                
            imgtk = ImageTk.PhotoImage(image=img)
            self.cam_canvas.imgtk = imgtk # Keep ref
            self.cam_canvas.config(image=imgtk)
            
            # Update Progress
            curr, total = progress
            if total > 0:
                self.progress['maximum'] = total
                self.progress['value'] = curr
                pct = int((curr / total) * 100)
                self.lbl_status.config(text=f"Receiving... {curr}/{total} ({pct}%)")
                
                if curr == total and not self.received_file_ready:
                    self.received_file_ready = True
                    self.lbl_status.config(text="Download Complete! Ready to save.")
                    self.btn_save.config(state='normal')
                    messagebox.showinfo("Success", "File received successfully!")
                    
        self.root.after(10, self.receiver_loop)

    def save_file(self):
        filename = filedialog.asksaveasfilename()
        if filename:
            try:
                self.decoder.save_current_file(filename)
                messagebox.showinfo("Saved", f"File saved to {filename}")
                # Reset
                self.received_file_ready = False
                self.btn_save.config(state='disabled')
                self.decoder.reset_session()
                self.progress['value'] = 0
                self.lbl_status.config(text="Ready")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
