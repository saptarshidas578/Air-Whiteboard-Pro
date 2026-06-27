# ✨ Air Whiteboard Pro

An AI-powered virtual whiteboard built using Computer Vision, Hand Gesture Recognition, and OCR technology. The system allows users to draw in the air using hand gestures without touching any physical device.

---

## 🚀 Features

### ✋ Hand Gesture Drawing

* Draw using your index finger.
* Real-time hand tracking using MediaPipe.
* Smooth drawing using exponential moving average filtering.

### 🎨 Dynamic Brush System

* Adjustable brush thickness using finger pinch distance.
* Multiple color selection:

  * Red
  * Green
  * Blue
  * White

### 🧹 Eraser Tool

* Four-finger gesture activates erasing mode.

### 📏 Shape Recognition

* Detects:

  * Circle
  * Rectangle
  * Triangle
* Converts rough sketches into clean shapes.

### 📄 Multi-Page Notes

* Create multiple whiteboard pages.
* Navigate between pages.
* Preserve drawings across pages.

### ↩ Undo Support

* Restore previous drawing states.

### 📷 Screenshot Capture

* Save camera frames instantly.

### 💾 Drawing Export

* Save individual drawings as PNG images.
* Export all pages into a PDF document.

### 🎥 Presentation Mode

* Hide interface elements for presentations and demonstrations.

### 🔤 AI OCR Integration

* Recognizes handwritten text using EasyOCR.
* OCR processing performed through a Flask server.
* Google Colab + ngrok integration for lightweight deployment.

---

## 🛠 Technologies Used

* Python
* OpenCV
* MediaPipe
* NumPy
* ReportLab
* Flask
* EasyOCR
* Requests
* Multithreading

---

## 📂 Project Structure

```text
Air-Whiteboard-Pro/
│
├── air_draw.py
├── requirements.txt
├── README.md
├── .gitignore
├── test_ocr.py
│
├── screenshots/
│
└── demo/
```

---

## ⚙ Installation

Clone the repository:

```bash
git clone https://github.com/saptarshidas578/Air-Whiteboard-Pro.git
cd Air-Whiteboard-Pro
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python air_draw.py
```

---

## ⌨ Keyboard Controls

| Key | Function          |
| --- | ----------------- |
| N   | New Page          |
| P   | Previous Page     |
| M   | Next Page         |
| C   | Clear Canvas      |
| U   | Undo              |
| S   | Save Drawing      |
| K   | Screenshot        |
| E   | Export PDF        |
| H   | Shape Recognition |
| O   | OCR Recognition   |
| T   | Presentation Mode |
| V   | Toggle Camera     |
| ESC | Exit              |

---

## 🎯 Applications

* Virtual classrooms
* Online teaching
* Presentations
* Digital note-taking
* Smart classrooms
* Gesture-based interfaces
* Human-computer interaction research

---

## Future Improvements

* Gesture shortcuts
* AI-based diagram recognition
* Voice commands
* Cloud note synchronization
* Multi-user collaboration

---

## 👨‍💻 Author

**Saptarshi Das**

Passionate about Computer Vision, Embedded Systems, AI, and Software Development.

GitHub:
https://github.com/saptarshidas578



## ⭐ If you like this project

Give the repository a star and share your feedback.
