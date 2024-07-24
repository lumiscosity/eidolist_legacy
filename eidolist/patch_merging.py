import filecmp
import os
import platform
import shutil
import subprocess
from os.path import exists

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QIcon, Qt, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QFileDialog, QWidget
from bs4 import BeautifulSoup

from eidolist.changelog_parser import parse_changelog, exists_untyped
from eidolist.lcf_parser import db_entries_from_changelog
from eidolist.message_box import MessageBox, ProgressBox, WarningBox
from eidolist.workdir import get_workdir
from eidolist.workers import Worker

loader = QUiLoader()


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


class PatchMergingWindow(QWidget):

    def __init__(self):
        super().__init__()

        # Clean up temp files, if any
        self.clean_temp_files(os.getcwd() + "/temp_main")
        self.clean_temp_files(os.getcwd() + "/temp_patch")

        self.patchdir = None
        self.threadpool = QThreadPool()
        self.warning_log = []
        self.main_copy_changed = []
        self.patch_changed = []
        self.patch_files = []
        self.workdir = get_workdir()

        # get the patch
        self.change_patchdir()
        if not self.patchdir:
            self.close()
            return

        self.progress = ProgressBox("Validating the changelog...", 100, self)
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)

        # validate the changelog
        self.load_patch()

        # final touches
        self.setWindowIcon(QIcon("icon.ico"))

    def change_patchdir(self):
        MessageBox(
            "Before proceeding, make sure that you have placed the changelog in the patch as **changelog.txt**."
        ).exec()

        new_patchdir = QFileDialog.getExistingDirectory(self, "Select the patch directory:", "/")
        if exists(new_patchdir):
            if exists(os.path.join(new_patchdir, "changelog.txt")):
                self.patchdir = new_patchdir
            else:
                MessageBox("Failed to find **changelog.txt**.").exec()
        elif new_patchdir != "":
            MessageBox("Failed to find the project folder.").exec()
        else:
            self.close()
            return

    def load_patch(self):
        # merging process starts here!
        # validate the patch changelog
        self.progress.show()
        self.warning_log = parse_changelog(self.patchdir, "check")

        for root, dirs, files in os.walk(self.patchdir):
            for i in files:
                if os.path.basename(self.patchdir) == os.path.basename(root):
                    if i[-3:] in {"ldb", "lmu", "lmt"}:
                        self.patch_files.append(i)

        # find every file and db entry changed so far in the main copy
        # this is saved in self.main_copy_changed
        self.main_copy_changed = parse_changelog(self.workdir, "list")

        # convert the lcf files
        self.progress.setMaximum(len(self.patch_files) * 2 - 2)
        self.progress.setLabelText("Converting LCF files...")

        worker = Worker(self.convert_lcf_files, self.patch_files, self.workdir, self.patchdir)
        worker.signals.progress.connect(self.bump_progress)
        worker.signals.result.connect(self.after_lcf_worker)

        self.threadpool.start(worker)

    def after_lcf_worker(self):
        # move new files to the patch;
        # if they already exist, and have been modified this patch, store them for later
        self.progress.setValue(0)
        self.progress.setLabelText("Merging patch assets...")

        patch_files = []
        for root, dirs, files in os.walk(self.patchdir):
            for i in files:
                if not os.path.basename(self.patchdir) == os.path.basename(root):
                    if i[-3:] not in {"ldb", "lmu", "lmt"}:
                        patch_files.append(os.path.basename(root) + '/' + i)
        self.progress.setMaximum(len(patch_files) - 1)

        self.progress.show()

        logged_files = []
        for i in self.main_copy_changed:
            for j in i:
                if j[-1] == "file":
                    logged_files.append(f"{i[0]}/{i[1]}")

        # this worker returns a list of conflicting files
        worker = Worker(self.merge_patch_assets, patch_files, logged_files, self.workdir, self.patchdir)
        worker.signals.progress.connect(self.bump_progress)
        worker.signals.result.connect(self.after_merge_worker)

        self.threadpool.start(worker)

    def after_merge_worker(self, conflicting_files):
        # ask about the conflicting files
        for i in range(len(conflicting_files)):
            dialog = loader.load("ui/file_merging.ui")
            dialog.setWindowIcon(QIcon("icon.ico"))

            dialog.mainCopyButton.clicked.connect(dialog.reject)
            dialog.patchButton.clicked.connect(dialog.accept)

            dialog.label.setText(dialog.label.text().replace("%1", conflicting_files[i]))

            # if the files are images, display them
            if conflicting_files[i][-3:] in ["png", "bmp"]:
                dialog.label_2.setPixmap(QPixmap(self.workdir + "/" + conflicting_files[i]))
                dialog.label_3.setPixmap(QPixmap(self.patchdir + "/" + conflicting_files[i]))

            if dialog.exec():
                self.merge_patch_version(self.workdir + "/" + conflicting_files[i], self.patchdir + "/" + conflicting_files[i])

        # ensure that all files mentioned in the LCFs exist

        self.progress.setValue(0)
        self.progress.setLabelText("Checking for files used in 2k3 data...")
        self.progress.setMaximum(len(self.patch_files))
        self.progress.show()

        worker = Worker(self.check_lcf_mentioned_files, self.patch_files, db_entries_from_changelog())
        worker.signals.progress.connect(self.bump_progress)
        worker.signals.result.connect(self.after_all_workers)

        self.threadpool.start(worker)

    def after_lcf_check_worker(self):
        pass

    def after_all_workers(self):
        if self.warning_log:
            fwarnings = ""
            for i in self.warning_log:
                fwarnings += "- " + i + "\n"
            WarningBox("Warning: mismatches in the patch were detected! Please correct them by placing the required "
                       "files in the main copy before continuing.",
                       fwarnings).exec()

    def bump_progress(self, n):
        self.progress.setValue(n)

    def convert_lcf_files(self, patch_files, workdir, patchdir, progress_callback):
        if platform.system() == "Windows":
            tool_call = f"{os.getcwd() + '/lcf2xml.exe'}"
        else:
            tool_call = "lcf2xml"
        for i in range(len(patch_files)):
            temp = '"' + patchdir + '/' + patch_files[i] + '"'
            subprocess.run((tool_call, temp))
            shutil.move(os.path.join(os.getcwd(), rreplace(patch_files[i], 'l', 'e', 1)),
                        os.path.join(os.getcwd(), "temp_patch", rreplace(patch_files[i], 'l', 'e', 1)))
            progress_callback.emit(2 * i - 1)

            temp = '"' + workdir + '/' + patch_files[i] + '"'
            subprocess.run(f"{os.getcwd() + '/lcf2xml.exe'} {temp}")
            shutil.move(os.path.join(os.getcwd(), rreplace(patch_files[i], 'l', 'e', 1)),
                        os.path.join(os.getcwd(), "temp_main", rreplace(patch_files[i], 'l', 'e', 1)))
            progress_callback.emit(2 * i)
        return patch_files

    def check_lcf_mentioned_files(self, patch_files, patch_db, progress_callback):
        print(patch_db)
        for i in os.listdir(f"{os.getcwd()}/temp_patch"):
            if i == "RPG_RT.edb":
                with open(os.getcwd() + "/temp_patch/RPG_RT.edb", encoding="utf-8") as file:
                    soup = BeautifulSoup(file, "lxml-xml", from_encoding="utf-8")
                    for j in patch_files["Animation"]:
                        # animations: file and sounds
                        anim = soup.LDB.Database.animations.find("Animation", id=j[1])
                        if not exists_untyped(f"{self.workdir}"
                                              f"{anim.animation_name}"):
                            self.warning_log.append(f"Animation file {anim.animation_name} used by animation "
                                                    f"{j[1]}, couldn't be found!")
                        for k in anim.find_all():
                            pass
            elif i == "RPG_RT.emt":
                pass
            else:  # lmu files
                pass
            progress_callback.emit(i)

    def merge_patch_assets(self, asset_list, match_list, workdir, patchdir, progress_callback):
        # this worker returns a list of merge conflicts
        out = []
        for i in range(len(asset_list)):
            # if the file hasn't been modified yet, is included but is the same as the main copy version
            # or is new, auto-merge it
            if asset_list[i][:-4] not in match_list or not exists(workdir + "/" + asset_list[i]):
                pass  # TODO: stubbed for testing; unstub this when done!
                # shutil.move(patchdir + "/" + asset_list[i], workdir + "/" + asset_list[i])
            elif not filecmp.cmp(patchdir + "/" + asset_list[i], workdir + "/" + asset_list[i], False):
                # else, add it to the list
                out.append(asset_list[i])
            progress_callback.emit(i)
        return out

    def clean_temp_files(self, dirpath):
        if exists(dirpath):
            for filename in os.listdir(dirpath):
                filepath = os.path.join(dirpath, filename)
                try:
                    shutil.rmtree(filepath)
                except OSError:
                    os.remove(filepath)

    def merge_patch_version(self, main_copy_file, patch_file):
        shutil.move(patch_file, main_copy_file)
