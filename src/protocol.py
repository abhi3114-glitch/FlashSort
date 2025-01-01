import zlib
import base64
import math
import hashlib
import json

class Packet:
    def __init__(self, file_id, sequence, total_chunks, payload):
        self.file_id = file_id
        self.sequence = sequence  # 0-indexed
        self.total_chunks = total_chunks
        self.payload = payload  # bytes

    def to_string(self):
        # Format: file_id:seq:total:crc32:b64_payload
        # payload is already bytes. We encode it to base64 string for safe transport.
        b64_data = base64.b64encode(self.payload).decode('ascii')
        
        # Calculate CRC of the ORIGINAL payload bytes, not the base64 string
        # This allows us to verify the data integrity independent of transport encoding
        crc = zlib.crc32(self.payload) & 0xFFFFFFFF
        
        # We use a simple delimiter format
        return f"{self.file_id}:{self.sequence}:{self.total_chunks}:{crc}:{b64_data}"

    @staticmethod
    def from_string(data_str):
        try:
            parts = data_str.split(':', 4)
            if len(parts) != 5:
                raise ValueError("Invalid packet format")
            
            file_id = parts[0]
            sequence = int(parts[1])
            total_chunks = int(parts[2])
            crc_claimed = int(parts[3])
            b64_data = parts[4]
            
            payload = base64.b64decode(b64_data)
            
            # Verify CRC
            crc_calc = zlib.crc32(payload) & 0xFFFFFFFF
            if crc_calc != crc_claimed:
                raise ValueError(f"CRC Mismatch: Expected {crc_claimed}, got {crc_calc}")
                
            return Packet(file_id, sequence, total_chunks, payload)
        except Exception as e:
            # print(f"Error parse packet: {e}") # Debug only
            return None

class FileChunker:
    def __init__(self, chunk_size=200):
        # 800 bytes payload results in ~1100 bytes QR packet (base64 + headers)
        # Version 40 QR can hold ~2-3KB, so 1KB is safe for lower versions/robustness
        self.chunk_size = chunk_size

    def chunk_file(self, file_path, file_id=None):
        if not file_id:
            # Generate a short hash as ID
            file_id = hashlib.md5(file_path.encode('utf-8')).hexdigest()[:8]

        packets = []
        with open(file_path, 'rb') as f:
            data = f.read()
            total_size = len(data)
            total_chunks = math.ceil(total_size / self.chunk_size)
            
            for i in range(total_chunks):
                start = i * self.chunk_size
                end = start + self.chunk_size
                chunk = data[start:end]
                packets.append(Packet(file_id, i, total_chunks, chunk))
                
        return packets

class FileReassembler:
    def __init__(self):
        self.active_transfers = {}  # {file_id: { 'chunks': {}, 'total': N, 'last_seen': time }}

    def add_packet(self, packet):
        if not packet:
            return None
            
        fid = packet.file_id
        if fid not in self.active_transfers:
            self.active_transfers[fid] = {
                'chunks': {},
                'total': packet.total_chunks,
                'received_count': 0
            }
        
        transfer = self.active_transfers[fid]
        
        # Only add if we haven't received this chunk yet
        if packet.sequence not in transfer['chunks']:
            transfer['chunks'][packet.sequence] = packet.payload
            transfer['received_count'] += 1
            
        return transfer['received_count'], transfer['total']

    def is_complete(self, file_id):
        if file_id not in self.active_transfers:
            return False
        transfer = self.active_transfers[file_id]
        return transfer['received_count'] == transfer['total']

    def save_file(self, file_id, output_path):
        if not self.is_complete(file_id):
            raise ValueError("File not complete")
            
        transfer = self.active_transfers[file_id]
        with open(output_path, 'wb') as f:
            for i in range(transfer['total']):
                f.write(transfer['chunks'][i])
        
        # Cleanup
        del self.active_transfers[file_id]
