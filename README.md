# XboxOS GUI

A simple desktop console-style launcher made with Python and Pygame.

## Features

- Clickable GUI launcher
- Keyboard navigation
- Xbox/gamepad navigation
- Built-in apps and games
- Windows executable build with PyInstaller
- App loading with useful error messages

## Included Apps

### Apps

- Help
- Mouse
- Sound
- Vibrate

### Games

- Pong
- Racing

## Requirements

- Windows 10/11
- Python 3.10+
- Pygame
- pynput
- PyInstaller (only needed for building)

Install everything with:

```bash
python -m pip install -r requirements.txt
```

## Running

```bash
python main.py
```

or on Windows:

```text
XboxOS.bat
```

## Building an EXE

Run the included build/setup wizard:

```text
setup.bat
```

It installs the requirements, checks PyInstaller, cleans old build output, and builds:

```text
dist\XboxOS\XboxOS.exe
```

The build uses the icon that actually exists in the repository:

```text
assets\Xbox.ico
```

## Project Structure

```text
XboxOS-GUI/
├── apps/
│   ├── games/
│   │   ├── pong.py
│   │   └── racing.py
│   ├── help.py
│   ├── mouse.py
│   ├── sound.py
│   └── vibrate.py
├── assets/
│   ├── background.png
│   ├── Car.png
│   ├── EnemyCAR.png
│   └── Xbox.ico
├── main.py
├── XboxOS.bat
├── setup.bat
├── requirements.txt
├── README.md
└── LICENSE
```

## Adding an App

Put a Python file in `apps/` or `apps/games/` and give it a callable `run()` function. Add an `App(...)` entry to `APP_LIST` in `main.py` to make it appear in the launcher.

## License

See `LICENSE` for the project license.

## Author

Created by **Iremide**.
