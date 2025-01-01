import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
from .protocol import FileReassembler, Packet
import threading
import time

class Decoder:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.reassembler = FileReassembler()
        self.running = False
        self.current_file_id = None
        self.last_progress = (0, 0)
        self.scanned_packets_this_session = set() # To track unique packets
        
    def start_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_index}")
        # Optimize camera for FPS if possible
        self.cap.set(cv2.CAP_PROP_FPS, 30) 
        self.running = True

    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame(self):
        """Reads a frame, decodes QRs, and updates reassembler. Returns the frame (annotated)."""
        if not self.cap or not self.running:
            return None, None

        ret, frame = self.cap.read()
        if not ret:
            return None, None

        # Detect QRs
        # ZBar is faster on grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decoded_objects = decode(gray, symbols=[ZBarSymbol.QRCODE])

        for obj in decoded_objects:
            try:
                data_str = obj.data.decode('utf-8')
                packet = Packet.from_string(data_str)
                
                if packet:
                    # Draw bounding box on frame
                    points = obj.polygon
                    if len(points) == 4:
                        pts = [(p.x, p.y) for p in points]
                        # Draw simple lines
                        for i in range(4):
                            cv2.line(frame, pts[i], pts[(i+1)%4], (0, 255, 0), 3)

                    # Update Reassembler
                    self.current_file_id = packet.file_id
                    
                    # Track unique packets just for immediate feedback statistics
                    packet_unique_id = f"{packet.file_id}:{packet.sequence}"
                    if packet_unique_id not in self.scanned_packets_this_session:
                        self.scanned_packets_this_session.add(packet_unique_id)
                        # Beep or visual flash could go here

                    current, total = self.reassembler.add_packet(packet)
                    self.last_progress = (current, total)
                    
            except Exception as e:
                # print(f"Decode error: {e}")
                pass
        
        return frame, self.last_progress

    def is_complete(self):
        if self.current_file_id:
            return self.reassembler.is_complete(self.current_file_id)
        return False

    def save_current_file(self, output_path):
        if self.current_file_id:
            self.reassembler.save_file(self.current_file_id, output_path)
            return True
        return False
        
    def reset_session(self):
        """Clear session data to be ready for new file"""
        self.scanned_packets_this_session.clear()
        self.current_file_id = None
        self.last_progress = (0, 0)
        # Note: We don't clear `active_transfers` in reassembler fully unless we want to discard partials.
        # But `scanned_packets_this_session` is just for UI metrics if needed.
