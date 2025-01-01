# FlashSort – Screen‑to‑Camera File Transfer

**FlashSort** is a Python‑only, offline solution for sending files between devices using a rapid stream of QR‑like visual barcodes. One device (the **sender**) displays a sequence of QR codes on its screen, while another device (the **receiver**) captures them with a webcam or a phone camera and reconstructs the original file.

---

## Table of Contents
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
  - [Sender (Desktop)](#sender-desktop)
  - [Receiver (Desktop)](#receiver-desktop)
  - [Receiver (Phone)](#receiver-phone)
- [Protocol Details](#protocol-details)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features
- **Pure Python** – No external services, works completely offline.
- **Cross‑platform** – Works on Windows, macOS and Linux.
- **Adjustable FPS** – Choose the transmission speed (5‑30 fps).
- **Integrity check** – CRC‑32 checksum per packet guarantees correct reconstruction.
- **Tkinter UI** – Simple, responsive graphical interface for both sender and receiver.
- **Mobile web receiver** – A lightweight HTML/JS page that runs on any phone browser (HTTPS not required on local network).

---

## Demo
![FlashSort Demo](https://raw.githubusercontent.com/abhi3114-glitch/FlashSort/main/assets/demo.gif)
*(The GIF shows a file being sent from a laptop and received on a phone.)*

---

## Installation
```bash
# Ensure you have Python 3.11 installed
py -3.11 -m pip install -r requirements.txt
```
The `requirements.txt` contains:
```
opencv-python
pillow
qrcode[pil]
pyzbar
numpy
```
> **Note**: On Windows you may need to install the Visual C++ Build Tools for `opencv-python`.

---

## Usage
### Sender (Desktop)
```bash
py -3.11 main.py
```
1. Choose **Sender** tab.
2. Click **Select File** and pick any file ≤ 20 MB.
3. Adjust **FPS** (default 10).
4. Click **Start Sending** – the screen will flash QR codes.

### Receiver (Desktop)
1. Open the same `main.py` program.
2. Switch to the **Receiver** tab.
3. Click **Start Camera** and allow webcam access.
4. Point the webcam at the sender’s screen.
5. When the progress bar reaches 100 % click **Save Received File**.

### Receiver (Phone)
1. Make sure the phone is on the same Wi‑Fi network as the laptop.
2. Start the mobile server (already running in the background):
   ```bash
   py -3.11 -m http.server 8080 --directory mobile
   ```
3. Open the phone browser and navigate to `http://<YOUR_LAPTOP_IP>:8080` (e.g., `http://192.168.1.42:8080`).
4. Tap **Start Camera** and grant permission.
5. Point the phone camera at the sender’s screen.
6. When the transfer finishes, tap **Download File**.

---

## Protocol Details
Each packet is a plain‑text string with the following fields, separated by `:`
```
file_id:seq_index:total_chunks:crc32:base64_payload
```
- `file_id` – a short identifier for the file (first 8 characters of a SHA‑256 hash).
- `seq_index` – zero‑based chunk number.
- `total_chunks` – total number of packets for the file.
- `crc32` – checksum of the original binary payload (before base64).
- `base64_payload` – the actual data chunk, encoded with URL‑safe Base64.

The receiver validates the CRC for each chunk and stores them in a temporary buffer. Once all chunks are received, they are concatenated and written to disk.

---

## Testing
```bash
py -3.11 test_logic.py
```
The test suite covers:
- Packet serialization / deserialization
- File chunking and re‑assembly
- CRC validation

---

## Troubleshooting
| Problem | Likely Cause | Fix |
|---|---|---|
| Camera permission denied | Browser blocks insecure origins | Enable *Insecure origins treated as secure* in Chrome (`chrome://flags`) or use HTTPS via a tunnel (ngrok). |
| No QR detected at low FPS | QR size too small or lighting poor | Increase QR size in `Encoder` (reduce `chunk_size`) or raise FPS to 5‑10. |
| Missing packets | Dropped frames | Lower FPS, improve camera focus, or increase `error_correction` level (`ERROR_CORRECT_M`). |
| Push fails (authentication) | No Git credentials | Configure a personal access token (`git remote set-url origin https://<TOKEN>@github.com/abhi3114-glitch/FlashSort.git`). |

---

## License
MIT License – see the `LICENSE` file.

---

*Happy flashing!*
