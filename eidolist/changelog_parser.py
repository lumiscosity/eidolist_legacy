import os
from datetime import date
from os.path import exists

from bs4 import BeautifulSoup

mt = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}

imt = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}

id_entries = [
    "map",
    "tileset",
    "v",
    "s",
    "ce",
    "actor",
    "animation"
]

ignore = [
    "connection",
    "connection from map"
    "bgm"
]


# Convenience function for getting data from and validating changelogs.
# Parse type can be "check" or "list".
# "Check" parsing checks for any errors in the changelog and returns the warning log.
# "List" parsing ignores most double checks, assuming they have been dealt with when merging,
# and returns the seen files instead.
def parse_changelog(directory: str, parse_type: str = "check"):
    warning_log = []

    with open(directory + "/changelog.txt") as file:
        changelog = file.read().splitlines()

    # Strip separators and start/end newlines
    if parse_type == "check":
        list(filter(lambda a: a != "|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|", changelog))
        while changelog[0] == "":
            del changelog[0]
        while changelog[-1] == "":
            del changelog[-1]

        seen_files = []
    else:
        seen_files = {}

    date_found = False
    for i in range(len(changelog)):
        # Minor validation check; in order to be positioned correctly, every changelog needs a date.
        date_found = changelog[i][:4] == "Date" or date_found

        # Ensure that the files / DB entries mentioned are present.
        try:
            if changelog[i][0] == "-":
                # File deletion is handled in a separate function at the end of the merging process;
                # for now, we just skip removed files.
                continue

            # Strip the starting entry
            elif changelog[i][0] in {"+", "*"}:
                log_entry = changelog[i].replace(" ", "", 1).replace("+", "").replace("*", "")
                # If there is a bracket, treat it as an ID component
                # The component then is a list of [root, ID, "id"].
                # Else, the component is a file component with a structure of [root_folder, filename, "file"].
                if log_entry.find("[") != -1:
                    component = [
                        log_entry[:log_entry.find("[")],
                        log_entry[log_entry.find("[") + 1:log_entry.find("]")],
                        "id"
                    ]
                else:
                    component = [
                        log_entry[:log_entry.find(" ")],
                        log_entry[log_entry.find(" ") + 1:],
                        "file"
                    ]

                # Maps are unique in that they have an ID, but are a file.
                if component[0].lower() == "map":
                    # Check
                    if parse_type == "check":
                        if not exists(directory + "\\Map" + component[1] + ".lmu"):
                            warning_log.append(
                                f"{component[0].capitalize() + component[1]} was mentioned in the changelog, but "
                                f"wasn't included in the patch!"
                            )
                        else:
                            seen_files.append((component[0] + component[1] + ".lmu").lower())
                    # List
                    else:
                        try:
                            seen_files["Map"].append(component[1])
                        except KeyError:
                            seen_files["Map"] = [component[1]]

                # All other ID components only need to be listed for the "list" parse type,
                # as they have no related files.
                elif component[-1] == "id":
                    if (parse_type == "list"
                            and component[0].lower() in id_entries
                            and component[0].lower() not in ignore
                    ):
                        try:
                            seen_files[component[0].capitalize()].append(component[1])
                        except KeyError:
                            seen_files[component[0].capitalize()] = [component[1]]

                # For file components, "check" verifies if the files exist, and "list" just lists them
                else:
                    # Check
                    if parse_type == "check":
                        if component[0].lower() == "charset" and not exists_untyped(
                                directory + "\\CharSet" + "\\" + component[1]
                        ):
                            warning_log.append(
                                f"{'CharSet/' + component[1]} was mentioned in the changelog, but "
                                f"wasn't included in the patch!"
                            )
                        elif component[0].lower() == "chipset" and not exists_untyped(
                                directory + "\\ChipSet" + "\\" + component[1]
                        ):
                            warning_log.append(
                                f"{'ChipSet/' + component[1]} was mentioned in the changelog, but "
                                f"wasn't included in the patch!"
                            )
                        elif not exists_untyped(directory + "\\" + component[0].capitalize() + "\\" + component[1]):
                            warning_log.append(
                                f"{component[0] + '/' + component[1]} was mentioned in the changelog, but "
                                f"wasn't included in the patch!"
                            )
                        for j in {".png", ".bmp", ".wav", ".mp3", ".ogg"}:
                            if exists(directory + "\\" + component[0] + "\\" + component[1] + j):
                                seen_files.append((component[0] + "\\" + component[1] + j).lower())
                    # List
                    elif (
                            exists(directory + "\\" + component[0].capitalize())
                            or component[0].lower() == "charset"
                            or component[0].lower() == "chipset"
                    ):
                        try:
                            # The folder capitalization for these two is unusual, so we need an override
                            if component[0].lower() == "charset":
                                seen_files["CharSet"].append(component[1])
                            elif component[0].lower() == "chipset":
                                seen_files["ChipSet"].append(component[1])
                            else:
                                seen_files[component[0].capitalize()].append(component[1])
                        except KeyError:
                            if component[0].lower() == "charset":
                                seen_files["CharSet"] = [component[1]]
                            elif component[0].lower() == "chipset":
                                seen_files["ChipSet"] = [component[1]]
                            else:
                                seen_files[component[0].capitalize()] = [component[1]]

        except IndexError:
            pass

    # Ensure that all files included have been mentioned in the changelog
    if parse_type == "check":
        patch_files = []
        for root, dirs, files in os.walk(directory):
            for i in files:
                if os.path.basename(directory) == os.path.basename(root):
                    # The LDB and LMU is checked separately
                    if i[:3] == "Map":
                        patch_files.append(i)
                else:
                    patch_files.append((os.path.basename(root) + '\\' + i))
        for i in patch_files:
            check = i.lower()
            if (check not in seen_files) and check[-3:] in {"lmu", "png", "bmp", "mp3", "wav", "ogg"}:
                warning_log.append(
                    f"{i[:-4]} was included in the patch, but wasn't mentioned in the changelog!".replace('\\', '/')
                )

    # Check if the changelog has a date
    if not date_found:
        warning_log.append("The changelog is missing a date!")

    if parse_type == "list":
        return seen_files

    return warning_log


# Merges a parsed changelog into the main changelog.
# Does operations on the main log.
def append_changelog(patch_log: list, main_log: list):
    # Minor safety measure
    if main_log[0] != "|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|":
        main_log.insert(0, "|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|")
    if main_log[-1] != "|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|":
        main_log.append("|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|")

    # Save and validate the date to position the changelog later
    for i in range(len(patch_log)):
        try:
            if patch_log[i][:4] == "Date":
                indate = patch_log[i][6:].split("/")
                # Numbers as months aren't valid, but we can let it slide and fix it here
                if indate[1] not in mt:
                    try:
                        indate[1] = imt[int(indate[1])]
                        patch_log[i] = f"Date: {indate[0]}/{indate[1]}/{indate[2]}"
                    except Exception:
                        return "Could not parse date"
                indate = date(int(indate[2]), mt[indate[1]], int(indate[0]))
        except IndexError:
            pass

    # Find a date greater than the current one or the EOF
    for i in range(len(main_log)):
        try:
            if main_log[i][:4] == "Date":
                chdate = main_log[i][6:].split("/")
                chdate = date(int(chdate[2]), mt[chdate[1]], int(chdate[0]))
                if indate < chdate:
                    break
        except IndexError:
            pass

    # We are now either at a valid date or at the EOF; look for the last separator
    while main_log[i] != "|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|":
        i -= 1

    # We are now at a separator; inserting the patch
    main_log.insert(i + 1, "|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|")
    main_log.insert(i + 1, "", )
    for j in patch_log:
        main_log.insert(i + 1, j)
    main_log.insert(i + 1, "", )


def exists_untyped(untyped_filepath):
    for i in {".png", ".bmp", ".wav", ".mp3", ".ogg"}:
        if exists(untyped_filepath + i):
            return True
    return False
