from PyQt5.QtWidgets import QWidget, QFormLayout, QLineEdit, QPushButton, QLabel
import rdflib

class InstanceEditor(QWidget):
    def __init__(self, ontology_viewer):
        super().__init__()
        self.ontology_viewer = ontology_viewer
        self.selected_class = None
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.selected_class_label = QLabel("No class selected")
        self.instance_uri_input = QLineEdit()
        self.instance_label_input = QLineEdit()
        self.instance_submit_button = QPushButton("Add Instance")
        self.instance_submit_button.clicked.connect(self.add_instance)
        
        self.layout.addRow(QLabel("Selected Class:"), self.selected_class_label)
        self.layout.addRow(QLabel("Instance URI:"), self.instance_uri_input)
        self.layout.addRow(QLabel("Label:"), self.instance_label_input)
        self.layout.addRow(self.instance_submit_button)
    
    def set_selected_class(self, class_uri):
        self.selected_class = class_uri
        self.selected_class_label.setText(class_uri)
    
    def add_instance(self):
        if not self.selected_class:
            print("No class selected")
            return
        
        instance_uri = self.instance_uri_input.text()
        label = self.instance_label_input.text()
        
        if instance_uri and label:
            instance = rdflib.URIRef(instance_uri)
            self.ontology_viewer.graph.add((instance, rdflib.RDF.type, rdflib.URIRef(self.selected_class)))
            self.ontology_viewer.graph.add((instance, rdflib.RDFS.label, rdflib.Literal(label, lang="en")))
            print(f"Added instance: {instance_uri} of class {self.selected_class} with label {label}")
            self.instance_uri_input.clear()
            self.instance_label_input.clear()