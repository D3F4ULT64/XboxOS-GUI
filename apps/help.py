import os


def get_python_files(folder):
    items = []

    if not os.path.exists(folder):
        return items

    for file in os.listdir(folder):
        if file.endswith(".py") and file != "__init__.py":
            items.append(file[:-3])

    return sorted(items)


def run():

    # apps folder
    apps_folder = os.path.dirname(os.path.abspath(__file__))

    # Check if asking for games
    import sys

    if len(sys.argv) > 2 and sys.argv[2] == "games":

        games_folder = os.path.join(
            apps_folder,
            "games"
        )

        games = get_python_files(games_folder)

        print("""
=========================
       XboxOS Games
=========================

Available Games
---------------
""")

        if games:
            for game in games:
                print("  " + game)
        else:
            print("  No games installed.")

        print("""
Usage:
    xboxos <game>

Example:
    xboxos pong
""")

        return


    # Normal apps help

    apps = get_python_files(apps_folder)

    print("""
=========================
        XboxOS
=========================

Available Apps
--------------
""")

    for app in apps:
        print("  " + app)


    print("""
Usage:
    xboxos <app>

Examples:
    xboxos mouse
    xboxos controller
    xboxos help games
""")