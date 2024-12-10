from PyQt5.QtWidgets import QWidget, QFormLayout, QComboBox, QPushButton, QLabel, QLineEdit
import rdflib

class WizardEditor(QWidget):
    def __init__(self, ontology_viewer):
        super().__init__()
        self.ontology_viewer = ontology_viewer
        self.selected_class = None
        self.property_class_pairs = []
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_selected)
        self.property_combo = QComboBox()
        self.property_combo.currentIndexChanged.connect(self.on_property_selected)
        
        self.instance_submit_button = QPushButton("Add Instance")
        self.instance_submit_button.clicked.connect(self.add_instance)
        
        self.instance_uri_input = QLineEdit()
        self.instance_label_input = QLineEdit()
        
        self.layout.addRow(QLabel("Select Class:"), self.class_combo)
        self.layout.addRow(QLabel("Select Property:"), self.property_combo)
        self.layout.addRow(QLabel("Instance URI:"), self.instance_uri_input)
        self.layout.addRow(QLabel("Instance Label:"), self.instance_label_input)
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
            UNION {{
                ?superclass rdfs:subClassOf <{self.selected_class}> .
                ?property rdfs:domain ?superclass
            }} UNION {{
                ?superclass rdfs:subClassOf <{self.selected_class}> .
                ?property rdfs:range ?superclass
            }}
        }}
        """
        self.execute_query(query, self.property_combo)
        self.property_combo.blockSignals(False)
    
    def on_class_selected(self):
        print("on_class_selected triggered")
        selected_class_uri = self.class_combo.currentData()
        if selected_class_uri:
            self.set_selected_class(selected_class_uri)
    
    def on_property_selected(self):
        print("on_property_selected triggered")
        selected_property_uri = self.property_combo.currentData()
        if selected_property_uri:
            new_class_combo = QComboBox()
            new_class_combo.currentIndexChanged.connect(self.on_class_selected_for_property)
            self.layout.addRow(QLabel("Select Class for Property:"), new_class_combo)
            self.property_class_pairs.append((selected_property_uri, new_class_combo))
            
            query = f"""
            SELECT ?class WHERE {{
                {{ <{selected_property_uri}> rdfs:domain ?class }} UNION {{ <{selected_property_uri}> rdfs:range ?class }}
            }}
            """
            self.execute_query(query, new_class_combo)
    
    def on_class_selected_for_property(self):
        print("on_class_selected_for_property triggered")
        selected_class_uri = self.sender().currentData()
        if selected_class_uri:
            new_property_combo = QComboBox()
            self.layout.addRow(QLabel("Select Property for Class:"), new_property_combo)
            self.property_class_pairs.append((selected_class_uri, new_property_combo))
            
            query = f"""
            SELECT ?property WHERE {{
                {{ ?property rdfs:domain <{selected_class_uri}> }} UNION {{ ?property rdfs:range <{selected_class_uri}> }}
                UNION {{
                    ?superclass rdfs:subClassOf <{selected_class_uri}> .
                    ?property rdfs:domain ?superclass
                }} UNION {{
                    ?superclass rdfs:subClassOf <{selected_class_uri}> .
                    ?property rdfs:range ?superclass
                }}
            }}
            """
            self.execute_query(query, new_property_combo)
    
    def add_instance(self):
        if not self.selected_class:
            print("No class selected")
            return
        
        instance_uri = self.instance_uri_input.text().strip()
        instance_label = self.instance_label_input.text().strip()
        
        if instance_uri and instance_label:
            instance = rdflib.URIRef(instance_uri)
            self.ontology_viewer.graph.add((instance, rdflib.RDF.type, rdflib.URIRef(self.selected_class)))
            self.ontology_viewer.graph.add((instance, rdflib.RDFS.label, rdflib.Literal(instance_label)))
            
            for prop_uri, class_combo in self.property_class_pairs:
                selected_class_uri = class_combo.currentData()
                if selected_class_uri:
                    self.ontology_viewer.graph.add((instance, rdflib.URIRef(prop_uri), rdflib.URIRef(selected_class_uri)))
            
            print(f"Added instance: {instance_uri} of class {self.selected_class} with label {instance_label}")
            self.clear_inputs()
    
    def clear_inputs(self):
        self.property_combo.clear()
        self.class_combo.clear()
        self.instance_uri_input.clear()
        self.instance_label_input.clear()
        for _, class_combo in self.property_class_pairs:
            class_combo.clear()
        self.property_class_pairs.clear()
    
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