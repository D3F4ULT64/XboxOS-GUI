# XboxOS GUI

A simple desktop operating system launcher made with Python and Pygame.

XboxOS GUI is a beginner-friendly version of XboxOS that replaces the command-line launcher with a graphical dashboard. Click an app to launch it instantly.

---

## Features

- 🖱️ Clickable GUI launcher
- 🎮 Built with Python and Pygame
- 📦 Simple app system
- 🕹️ Built-in games
- 💻 Easy to extend with new apps
- 🪟 Windows executable support using PyInstaller

---

## Included Apps

### Apps

- Help
- Mouse
- Sound
- Vibrate

### Games

- Pong
- Racing

---

## Requirements

- Python 3.13 or newer
- Pygame
- pynput (Mouse app)

Install requirements:

```bash
pip install -r requirements.txt
```

---

## Running XboxOS

Run with Python:

```bash
python main.py
```

or

```bash
py main.py
```

---

## Building an EXE

Run:

```bash
build.bat
```

or manually:

```bash
py -m PyInstaller --onedir --windowed --icon=assets\xboxos.ico --name XboxOS main.py
```

The executable will be created in:

```
dist\XboxOS\
```

---

## Project Structure

```
XboxOS_GUI/
│
├── apps/
│   ├── games/
│   │   ├── pong.py
│   │   └── racing.py
│   ├── help.py
│   ├── mouse.py
│   ├── sound.py
│   └── vibrate.py
│
├── assets/
│   └── xboxos.ico
│
├── build.bat
├── main.py
├── README.md
├── requirements.txt
└── LICENSE
```

---

## Future Plans

- Controller navigation
- Xbox-style dashboard
- App icons
- Animations
- Themes
- Settings
- More games
- Better app management

---

## License

See the LICENSE file.

---

## Author

Created by **Iremide**

GitHub: https://github.com/D3F4ULT64

Email: d3f4ult.os@gmail.com