class Directory:
    def __init__(self, name, parent = None):
        self.name = name
        self.parent = parent
        self.subdirectories = []
        self.files = []