import sys
from PyQt5.QtWidgets import QApplication
from ontology_viewer import OntologyViewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OntologyViewer()
    window.show()
    sys.exit(app.exec_())