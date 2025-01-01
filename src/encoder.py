import qrcode
from PIL import Image
from .protocol import FileChunker

class Encoder:
    def __init__(self, chunk_size=200, error_correction=qrcode.constants.ERROR_CORRECT_M):
        self.chunker = FileChunker(chunk_size)
        self.error_correction = error_correction
        self.packets = []
        
    def load_file(self, file_path):
        self.packets = self.chunker.chunk_file(file_path)
        return len(self.packets)
        
    def generate_frames(self):
        """Generator that yields PIL images for each packet."""
        if not self.packets:
            return

        # Pre-configure the QR factory for performance? 
        # Actually creating a new QRCode object for each frame is safer to avoid state overlap, 
        # though resetting is possible. 
        
        for packet in self.packets:
            qr = qrcode.QRCode(
                version=None, # Auto-size
                error_correction=self.error_correction,
                box_size=10,
                border=4,
            )
            qr.add_data(packet.to_string())
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            yield img

    def get_packet_count(self):
        return len(self.packets)
