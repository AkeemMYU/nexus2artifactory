import json
from ..core import Menu
from . import Setup, Repo, Safety

# The main menu. This is the first menu that appears when the tool is started,
# and it's the hub that everything else can be accessed through. It contains
# special options for saving and loading a configuration to and from a file,
# running verification on an entire configuration at any time, and running a
# full migration based on the current configuration.
class Main(Menu):
    # Initialize the main menu by setting up the options.
    def __init__(self, scr):
        Menu.__init__(self, scr, "Nexus -> Artifactory")
        self.saveopt = self.mkopt('s', "Save Configuration", ['|', self.save])
        self.loadopt = self.mkopt('l', "Load Configuration",
                                  [self.preload, '|', self.load])
        self.repopt = self.mkopt('r', "Repository Migration Setup", Repo(scr))
        self.opts = [
            self.mkopt('i', "Initial Setup", [Setup(scr), self.statrefresh]),
            self.repopt,
            None,
            self.saveopt,
            self.loadopt,
            self.mkopt('v', "Verify Configuration", self.doverify),
            self.mkopt('x', "Run Migration", self.runmigration),
            None,
            self.mkopt('h', "Help", '?'),
            self.mkopt('q', "Exit", None, hdoc=False)]

    # When setup runs, refresh the view, as there may be new statuses.
    def statrefresh(self, _):
        self.repopt['stat'] = self.repopt['act'][0].verify()
        self.scr.msg = None

    # Run full verification on the configuration, using the menu's verify()
    # function. Print the result.
    def doverify(self, _):
        if self.verify():
            self.scr.msg = ('val', "Configuration verified successfully.")
        else: self.scr.msg = ('err', "Configuration verified, errors found.")

    # Run the actual migration, and print the result.
    def runmigration(self, _):
        if not self.verify():
            self.scr.msg = ('err', "Cannot run migration, errors found.")
            return
        status = self.scr.artifactory.migrate(self.collectconf())
        if status == True: self.scr.msg = ('val', "Migration successful!")
        else: self.scr.msg = ('err', "Migration error: " + status)

    # Serialize the current configuration state as a JSON object, and save it to
    # a file. The parameter 'sel' is the menu option that ran this function.
    def save(self, sel):
        if sel['val'] == None: return
        f = None
        try:
            f = open(sel['val'], 'w')
            conf = self.collectconf()
            if 'Save Configuration' in conf: del conf['Save Configuration']
            if 'Load Configuration' in conf: del conf['Load Configuration']
            json.dump(conf, f, indent=4)
            self.scr.msg = ('val', "Successfully saved to specified file.")
            sel['stat'] = True
        except:
            self.scr.msg = ('err', "Unable to save to specified file.")
            sel['stat'] = False
        finally:
            if f != None: f.close()
        if sel['stat'] == True and self.loadopt['val'] == None:
            self.loadopt['val'] = sel['val']
        self.scr.modified = None

    # Before loading a JSON object from a file, if there are unsaved changes,
    # ensure that the user wants to discard them.
    def preload(self, sel):
        if self.scr.modified and not Safety(self.scr).show(): return False

    # Load a JSON object from a file, and apply the configuration state
    # specified by that object as the current state. The parameter 'sel' is the
    # menu option that ran this function.
    def load(self, sel):
        value = sel['val']
        if sel['val'] == None: return
        f = None
        try:
            f = open(sel['val'], 'r')
            self.applyconf(json.load(f))
            if self.verify():
                self.scr.msg = ('val', "Configuration loaded successfully.")
            else:
                self.scr.msg = ('err', "Configuration loaded, errors found.")
            sel['stat'] = True
        except:
            self.scr.msg = ('err', "Unable to load from specified file.")
            sel['stat'] = False
        finally:
            if f != None: f.close()
        sel['val'] = value
        if sel['stat'] == True and self.saveopt['val'] == None:
            self.saveopt['val'] = sel['val']
        self.scr.modified = None
