import sys
import unittest
import os
from src.protocol import Packet, FileChunker, FileReassembler
from src.encoder import Encoder
# We won't test full zbar decoding in unit test as it requires image loaded, but we can test logic.

class TestFlashSort(unittest.TestCase):
    def test_packet_encoding_decoding(self):
        payload = b"Hello World"
        pkt = Packet("file1", 0, 1, payload)
        s = pkt.to_string()
        pkt2 = Packet.from_string(s)
        self.assertEqual(pkt2.payload, payload)
        self.assertEqual(pkt2.file_id, "file1")
        
    def test_chunking(self):
        # Create dummy file
        with open("test.txt", "wb") as f:
            f.write(b"A" * 2000)
            
        chunker = FileChunker(chunk_size=800)
        packets = chunker.chunk_file("test.txt")
        self.assertEqual(len(packets), 3) # 800, 800, 400
        
        reassembler = FileReassembler()
        for p in packets:
            reassembler.add_packet(p)
            
        self.assertTrue(reassembler.is_complete(packets[0].file_id))
        reassembler.save_file(packets[0].file_id, "test_out.txt")
        
        with open("test_out.txt", "rb") as f:
            data = f.read()
        self.assertEqual(len(data), 2000)
        
        # Clean up
        os.remove("test.txt")
        os.remove("test_out.txt")
        
if __name__ == '__main__':
    unittest.main()
