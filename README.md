# XboxOS

XboxOS is a Python and Pygame project inspired by modern game console dashboards.

It is a hobby project focused on creating a simple console-style desktop experience with controller support, games, apps, and a custom interface.

## Features

### Current Features

* Built with Python and Pygame
* Fullscreen interface
* Xbox controller support
* Keyboard support
* Mouse support
* Custom assets support
* Game and app folder structure
* Setup wizard for installing requirements
* Windows launcher support

### Planned Features

Future updates may include:

* More built-in apps
* More games
* Improved animations
* Custom themes
* Settings system
* More controller features
* Additional Xbox-style features

## Requirements

* Windows 10 or Windows 11
* Python 3.13 or newer
* Pygame

## Installation

1. Download or clone this repository.
2. Run `setup.bat`.
3. Follow the setup wizard.
4. Launch XboxOS using `XboxOS.bat` or:

```text
python main.py
```

## Portable Copy Warning

The setup wizard includes an option to copy the XboxOS folder to another location.

**Warning:** Some versions of XboxOS use fixed file paths for assets. Copying the folder may cause:

* Missing images
* Missing sounds
* Apps failing to load correctly
* Other unexpected issues

This will be improved in future versions by using relative file paths.

## Project Structure

```text
XboxOS/
│
├── setup.bat
├── XboxOS.bat
├── LICENSE
├── README.md
├── requirements.txt
├── main.py
│
├── assets/
│   ├── background.png
│   ├── Car.png
│   └── EnemyCAR.png
│
├── apps/
│
└── games/
```

## Controller Support

XboxOS supports Xbox controllers through Python and Pygame.

Supported input includes:

* Controller buttons
* Joystick movement
* Game controls

## Development Status

XboxOS is currently in **early development**.

New features, games, apps, and improvements are added regularly as the project grows.

## License

XboxOS is licensed under **All Rights Reserved**.

You may:

* View the source code.
* Learn from the project.
* Use XboxOS for personal purposes.

You may not:

* Sell XboxOS.
* Claim XboxOS as your own creation.
* Redistribute XboxOS without permission.
* Remove or alter copyright notices.

See the `LICENSE` file for complete license information.

## Contact

Questions, bug reports, feature requests, and suggestions are always welcome.

Email: [d3f4ult.os@gmail.com](mailto:d3f4ult.os@gmail.com)

## About

XboxOS is an independent hobby project created by **D3f4ult**.

The project is built using Python and Pygame with the goal of creating a console-inspired desktop experience.

Copyright © 2026 D3f4ult. All rights reserved.
