from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QComboBox
import rdflib

class TripleWizard(QWidget):
    def __init__(self, ontology_viewer):
        super().__init__()
        self.ontology_viewer = ontology_viewer
        self.selected_class = None
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.class_label = QLabel("Selected Class: None")
        self.subject_input = QLineEdit()
        self.predicate_combo = QComboBox()
        self.object_input = QLineEdit()
        self.add_triple_button = QPushButton("Add Triple")
        self.add_triple_button.clicked.connect(self.add_triple)
        
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Subject:"), self.subject_input)
        form_layout.addRow(QLabel("Predicate:"), self.predicate_combo)
        form_layout.addRow(QLabel("Object:"), self.object_input)
        form_layout.addRow(self.add_triple_button)
        
        self.layout.addWidget(self.class_label)
        self.layout.addLayout(form_layout)
    
    def set_selected_class(self, class_uri):
        self.selected_class = class_uri
        self.class_label.setText(f"Selected Class: {class_uri}")
        self.populate_predicates()
    
    def populate_predicates(self):
        self.predicate_combo.clear()
        query = f"""
        SELECT ?property WHERE {{
            ?property rdfs:domain <{self.selected_class}> .
        }}
        """
        for row in self.ontology_viewer.graph.query(query):
            property_uri = str(row[0])
            property_short = self.ontology_viewer.extract_last_part(property_uri)
            self.predicate_combo.addItem(property_short, property_uri)
    
    def add_triple(self):
        subject = self.subject_input.text()
        predicate = self.predicate_combo.currentData()
        object_ = self.object_input.text()
        
        if subject and predicate and object_:
            subject_uri = rdflib.URIRef(subject)
            predicate_uri = rdflib.URIRef(predicate)
            object_uri = rdflib.URIRef(object_)
            self.ontology_viewer.graph.add((subject_uri, predicate_uri, object_uri))
            print(f"Added triple: ({subject}, {predicate}, {object_})")
            self.subject_input.clear()
            self.object_input.clear()