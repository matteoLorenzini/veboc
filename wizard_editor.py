from PyQt5.QtWidgets import QWidget, QFormLayout, QComboBox, QPushButton, QLabel
import rdflib

class WizardEditor(QWidget):
    def __init__(self, ontology_viewer):
        super().__init__()
        self.ontology_viewer = ontology_viewer
        self.selected_class = None
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_selected)
        self.property_combo = QComboBox()
        self.property_combo.currentIndexChanged.connect(self.on_property_selected)
        
        self.instance_submit_button = QPushButton("Add Instance")
        self.instance_submit_button.clicked.connect(self.add_instance)
        
        self.layout.addRow(QLabel("Select Class:"), self.class_combo)
        self.layout.addRow(QLabel("Select Property:"), self.property_combo)
        self.layout.addRow(self.instance_submit_button)
    
    def set_selected_class(self, class_uri):
        self.selected_class = class_uri
        self.update_properties()
    
    def update_properties(self):
        self.property_combo.blockSignals(True)
        self.property_combo.clear()
        query = f"""
        SELECT ?property WHERE {{
            {{ ?property rdfs:domain <{self.selected_class}> }} UNION {{ ?property rdfs:range <{self.selected_class}> }}
        }}
        """
        self.execute_query(query, self.property_combo)
        self.property_combo.blockSignals(False)
    
    def on_class_selected(self):
        print("on_class_selected triggered")
        self.property_combo.blockSignals(True)
        self.property_combo.clear()
        selected_class_uri = self.class_combo.currentData()
        if selected_class_uri:
            query = f"""
            SELECT ?property WHERE {{
                {{ ?property rdfs:domain <{selected_class_uri}> }} UNION {{ ?property rdfs:range <{selected_class_uri}> }}
            }}
            """
            self.execute_query(query, self.property_combo)
        self.property_combo.blockSignals(False)
    
    def on_property_selected(self):
        print("on_property_selected triggered")
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        selected_property_uri = self.property_combo.currentData()
        if selected_property_uri:
            query = f"""
            SELECT ?class WHERE {{
                {{ <{selected_property_uri}> rdfs:domain ?class }} UNION {{ <{selected_property_uri}> rdfs:range ?class }}
            }}
            """
            self.execute_query(query, self.class_combo)
        self.class_combo.blockSignals(False)
    
    def add_instance(self):
        if not self.selected_class:
            print("No class selected")
            return
        
        selected_property_uri = self.property_combo.currentData()
        selected_class_uri = self.class_combo.currentData()
        
        if selected_property_uri and selected_class_uri:
            instance = rdflib.URIRef(selected_property_uri)
            self.ontology_viewer.graph.add((instance, rdflib.RDF.type, rdflib.URIRef(self.selected_class)))
            self.ontology_viewer.graph.add((instance, rdflib.RDFS.label, rdflib.URIRef(selected_class_uri)))
            print(f"Added instance: {selected_property_uri} of class {self.selected_class} with label {selected_class_uri}")
            self.property_combo.clear()
            self.class_combo.clear()
    
    def execute_query(self, query, combo_box):
        print(f"Executing query: {query}")
        try:
            for row in self.ontology_viewer.graph.query(query):
                uri = str(row[0])
                short_name = self.ontology_viewer.extract_last_part(uri)
                combo_box.addItem(short_name, uri)
        except Exception as e:
            print(f"Error executing query: {e}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    ontology_viewer = None  # Replace with actual ontology viewer instance
    window = WizardEditor(ontology_viewer)
    window.show()
    sys.exit(app.exec_())