import os
from PyQt5.QtWidgets import QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QTextBrowser, QSplitter, QTabWidget, QComboBox, QTreeWidgetItemIterator, QLineEdit, QLabel
from PyQt5.QtCore import Qt
import rdflib
from instance_editor import InstanceEditor
from wizard_editor import WizardEditor
from reasoning_engine import ReasoningEngine

class OntologyViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ontology Viewer")
        
        self.upload_button = QPushButton("Upload Ontology")
        self.upload_button.clicked.connect(self.upload_ontology)
        
        self.save_button = QPushButton("Save Ontology")
        self.save_button.clicked.connect(self.save_ontology)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search entities, properties, instances...")
        self.search_bar.returnPressed.connect(self.search_ontology)
        
        self.preloaded_combo = QComboBox()
        self.preloaded_combo.addItem("Select Preloaded Ontology")
        self.preloaded_combo.activated[str].connect(self.load_preloaded_ontology)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Ontology Classes")
        self.tree.itemClicked.connect(self.on_class_item_clicked)
        
        self.object_properties_tree = QTreeWidget()
        self.object_properties_tree.setHeaderLabel("Object Properties")
        self.object_properties_tree.itemClicked.connect(self.on_property_item_clicked)
        
        self.populated_tree = QTreeWidget()
        self.populated_tree.setHeaderLabel("Populated Ontology")
        self.populated_tree.itemClicked.connect(self.on_instance_item_clicked)
        
        self.info = QTextBrowser()
        self.info.setOpenExternalLinks(False)
        self.info.anchorClicked.connect(self.on_anchor_clicked)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tree, "Ontology Classes")
        self.tabs.addTab(self.object_properties_tree, "Object Properties")
        self.tabs.addTab(self.populated_tree, "Populated Ontology")
        
        self.instance_editor = InstanceEditor(self)
        self.tabs.addTab(self.instance_editor, "Instance Editor")
        
        self.wizard_editor = WizardEditor(self)
        self.tabs.addTab(self.wizard_editor, "Wizard Editor")
        
        layout = QVBoxLayout()
        layout.addWidget(self.upload_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.preloaded_combo)
        layout.addWidget(self.tabs)
        
        left_container = QWidget()
        left_container.setLayout(layout)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.info)
        
        right_container = QWidget()
        right_container.setLayout(right_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(splitter)
        container.setLayout(container_layout)
        
        self.setCentralWidget(container)
        
        self.graph = rdflib.Graph()
        self.class_uri_map = {}
        self.property_uri_map = {}
        
        self.preloaded_folder = "preloaded_ontologies"
        self.load_preloaded_ontologies()
        
        self.reasoning_engine = ReasoningEngine(self.graph)
        
        self.reason_button = QPushButton("Apply Reasoning")
        self.reason_button.clicked.connect(self.apply_reasoning)
        layout.addWidget(self.reason_button)
        
    def apply_reasoning(self):
        self.reasoning_engine.apply_reasoning()
        self.visualize_ontology()
        self.display_object_properties()
        self.visualize_populated_ontology()
        
    def load_preloaded_ontologies(self):
        if not os.path.exists(self.preloaded_folder):
            os.makedirs(self.preloaded_folder)
        for filename in os.listdir(self.preloaded_folder):
            if filename.endswith(".owl") or filename.endswith(".rdf"):
                self.preloaded_combo.addItem(filename)
    
    def load_preloaded_ontology(self, filename):
        if filename != "Select Preloaded Ontology":
            file_path = os.path.join(self.preloaded_folder, filename)
            self.load_ontology(file_path)
            self.visualize_ontology()
            self.display_object_properties()
            self.visualize_populated_ontology()
    
    def upload_ontology(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Ontology", "", "OWL files (*.owl);;RDF files (*.rdf)")
        if file_path:
            self.load_ontology(file_path)
            self.visualize_ontology()
            self.display_object_properties()
            self.visualize_populated_ontology()
    
    def save_ontology(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Ontology", "", "OWL files (*.owl);;RDF files (*.rdf)")
        if file_path:
            self.graph.serialize(destination=file_path, format='xml')
            print(f"Ontology saved to {file_path}")
    
    def load_ontology(self, file_path):
        self.graph.parse(file_path)
    
    def visualize_ontology(self):
        self.tree.clear()
        self.class_uri_map.clear()
        query = """
        SELECT ?class ?subclass WHERE {
            ?subclass rdfs:subClassOf ?class .
        }
        """
        class_hierarchy = {}
        for row in self.graph.query(query):
            parent = str(row[0])
            child = str(row[1])
            parent_short = self.extract_last_part(parent)
            child_short = self.extract_last_part(child)
            self.class_uri_map[parent_short] = parent
            self.class_uri_map[child_short] = child
            if parent_short not in class_hierarchy:
                class_hierarchy[parent_short] = []
            class_hierarchy[parent_short].append(child_short)
        
        root_classes = [cls for cls in class_hierarchy if all(cls not in children for children in class_hierarchy.values())]
        
        for root_class in root_classes:
            root_item = QTreeWidgetItem([root_class])
            self.tree.addTopLevelItem(root_item)
            self.add_children(root_item, root_class, class_hierarchy)
    
    def add_children(self, parent_item, parent_class, class_hierarchy):
        if parent_class in class_hierarchy:
            for child_class in class_hierarchy[parent_class]:
                child_item = QTreeWidgetItem([child_class])
                parent_item.addChild(child_item)
                self.add_children(child_item, child_class, class_hierarchy)
    
    def display_object_properties(self):
        self.object_properties_tree.clear()
        self.property_uri_map.clear()
        query = """
        SELECT ?property ?label ?domain ?range WHERE {
            ?property a owl:ObjectProperty .
            OPTIONAL { ?property rdfs:label ?label . }
            OPTIONAL { ?property rdfs:domain ?domain . }
            OPTIONAL { ?property rdfs:range ?range . }
            FILTER (lang(?label) = 'en' || lang(?label) = '')
        }
        """
        property_hierarchy = {}
        for row in self.graph.query(query):
            property = str(row[0])
            label = str(row[1]) if row[1] else ""
            domain = str(row[2]) if row[2] else ""
            range_ = str(row[3]) if row[3] else ""
            property_short = self.extract_last_part(property)
            self.property_uri_map[property_short] = property
            self.property_uri_map[property] = property  # Add full URI to map
            property_hierarchy[property_short] = (label, domain, range_)
        
        for property, (label, domain, range_) in property_hierarchy.items():
            property_item = QTreeWidgetItem([property])
            self.object_properties_tree.addTopLevelItem(property_item)
    
    def visualize_populated_ontology(self):
        self.populated_tree.clear()
        self.class_uri_map.clear()
        query = """
        SELECT ?class ?subclass WHERE {
            ?subclass rdfs:subClassOf ?class .
        }
        """
        class_hierarchy = {}
        for row in self.graph.query(query):
            parent = str(row[0])
            child = str(row[1])
            parent_short = self.extract_last_part(parent)
            child_short = self.extract_last_part(child)
            self.class_uri_map[parent_short] = parent
            self.class_uri_map[child_short] = child
            if parent_short not in class_hierarchy:
                class_hierarchy[parent_short] = []
            class_hierarchy[parent_short].append(child_short)
        
        root_classes = [cls for cls in class_hierarchy if all(cls not in children for children in class_hierarchy.values())]
        
        for root_class in root_classes:
            root_item = QTreeWidgetItem([root_class])
            self.populated_tree.addTopLevelItem(root_item)
            self.add_children_with_instances(root_item, root_class, class_hierarchy)
    
    def add_children_with_instances(self, parent_item, parent_class, class_hierarchy):
        if parent_class in class_hierarchy:
            for child_class in class_hierarchy[parent_class]:
                child_item = QTreeWidgetItem([child_class])
                parent_item.addChild(child_item)
                self.add_children_with_instances(child_item, child_class, class_hierarchy)
                self.add_instances(child_item, self.class_uri_map[child_class])
    
    def add_instances(self, class_item, class_uri):
        query = f"""
        SELECT ?instance WHERE {{
            ?instance a <{class_uri}> .
        }}
        """
        for row in self.graph.query(query):
            instance_uri = str(row[0])
            instance_short = self.extract_last_part(instance_uri)
            instance_item = QTreeWidgetItem([instance_short])
            class_item.addChild(instance_item)
    
    def on_class_item_clicked(self, item, column):
        selected_class_short = item.text(column)
        print(f"Selected class short: {selected_class_short}")  # Debugging statement
        if selected_class_short in self.class_uri_map:
            selected_class = self.class_uri_map[selected_class_short]
            self.display_class_info(selected_class)
            self.instance_editor.set_selected_class(selected_class)
            self.wizard_editor.set_selected_class(selected_class)
        else:
            print(f"Error: {selected_class_short} not found in class_uri_map")  # Debugging statement
    
    def display_class_info(self, selected_class):
        query = f"""
        SELECT ?property ?value WHERE {{
            <{selected_class}> ?property ?value .
            FILTER (lang(?value) = 'en' || lang(?value) = '')
        }}
        """
        info_text = f"<h2>Class: <a href='{selected_class}'>{self.extract_last_part(selected_class)}</a></h2>\n"
        info_text += "<h3>Properties:</h3>\n"
        for row in self.graph.query(query):
            property = str(row[0])
            value = str(row[1])
            property_short = self.extract_last_part(property)
            value_short = self.extract_last_part(value)
            if value in self.class_uri_map.values() or value in self.property_uri_map.values():
                value_short = f"<a href='{value}'>{value_short}</a>"
            info_text += f"<p><strong>{property_short}:</strong> {value_short}</p>\n"
        self.info.setHtml(info_text)
    
    def on_property_item_clicked(self, item, column):
        selected_property_short = item.text(column)
        print(f"Selected property short: {selected_property_short}")  # Debugging statement
        if selected_property_short in self.property_uri_map:
            selected_property = self.property_uri_map[selected_property_short]
            self.display_property_info(selected_property)
        else:
            print(f"Error: {selected_property_short} not found in property_uri_map")  # Debugging statement
    
    def on_instance_item_clicked(self, item, column):
        parent = item.parent()
        if parent:
            class_short = parent.text(0)
            if class_short in self.class_uri_map:
                instance_short = item.text(0)
                instance_uri = None
                query = f"""
                SELECT ?instance WHERE {{
                    ?instance a <{self.class_uri_map[class_short]}> .
                }}
                """
                for row in self.graph.query(query):
                    if self.extract_last_part(str(row[0])) == instance_short:
                        instance_uri = str(row[0])
                        break
                if instance_uri:
                    self.display_instance_info(instance_uri)
    
    def display_instance_info(self, instance_uri):
        query = f"""
        SELECT ?property ?value WHERE {{
            <{instance_uri}> ?property ?value .
            FILTER (lang(?value) = 'en' || lang(?value) = '')
        }}
        """
        info_text = f"<h2>Instance: <a href='{instance_uri}'>{self.extract_last_part(instance_uri)}</a></h2>\n"
        info_text += "<h3>Properties:</h3>\n"
        for row in self.graph.query(query):
            property = str(row[0])
            value = str(row[1])
            property_short = self.extract_last_part(property)
            value_short = self.extract_last_part(value)
            if value in self.class_uri_map.values() or value in self.property_uri_map.values():
                value_short = f"<a href='{value}'>{value_short}</a>"
            info_text += f"<p><strong>{property_short}:</strong> {value_short}</p>\n"
        self.info.setHtml(info_text)
    
    def display_property_info(self, selected_property):
        query = f"""
        SELECT ?label ?domain ?range WHERE {{
            <{selected_property}> rdfs:label ?label .
            OPTIONAL {{ <{selected_property}> rdfs:domain ?domain . }}
            OPTIONAL {{ <{selected_property}> rdfs:range ?range . }}
            FILTER (lang(?label) = 'en' || lang(?label) = '')
        }}
        """
        info_text = f"<h2>Property: <a href='{selected_property}'>{self.extract_last_part(selected_property)}</a></h2>\n"
        info_text += "<h3>Details:</h3>\n"
        for row in self.graph.query(query):
            label = str(row[0])
            domain = str(row[1]) if row[1] else ""
            range_ = str(row[2]) if row[2] else ""
            domain_short = self.extract_last_part(domain)
            range_short = self.extract_last_part(range_)
            if domain in self.class_uri_map.values() or domain in self.property_uri_map.values():
                domain_short = f"<a href='{domain}'>{domain_short}</a>"
            if range_ in self.class_uri_map.values() or range_ in self.property_uri_map.values():
                range_short = f"<a href='{range_}'>{range_short}</a>"
            info_text += f"<p><strong>Label:</strong> {label}</p>\n"
            info_text += f"<p><strong>Domain:</strong> {domain_short}</p>\n"
            info_text += f"<p><strong>Range:</strong> {range_short}</p>\n"
        self.info.setHtml(info_text)
    
    def search_ontology(self):
        search_text = self.search_bar.text().strip().lower()
        if not search_text:
            return
        
        results = []
        
        # Search classes
        for class_short, class_uri in self.class_uri_map.items():
            if search_text in class_short.lower():
                results.append((class_short, class_uri))
        
        # Search properties
        for property_short, property_uri in self.property_uri_map.items():
            if search_text in property_short.lower():
                results.append((property_short, property_uri))
        
        # Search instances
        query = """
        SELECT ?instance WHERE {
            ?instance a ?class .
        }
        """
        for row in self.graph.query(query):
            instance_uri = str(row[0])
            instance_short = self.extract_last_part(instance_uri)
            if search_text in instance_short.lower():
                results.append((instance_short, instance_uri))
            
        # Display results
        if results:
            info_text = "<h2>Search Results:</h2>\n<ul>"
            for result_short, result_uri in results:
                info_text += f"<li><a href='{result_uri}'>{result_short}</a></li>\n"
            info_text += "</ul>"
            self.info.setHtml(info_text)
        else:
            self.info.setHtml("<h2>No results found</h2>")
    
    def on_anchor_clicked(self, url):
        uri = url.toString()
        print(f"Clicked URI: {uri}")  # Debugging statement
        if uri in self.class_uri_map.values():
            self.display_class_info(uri)
            self.expand_tree_item(self.tree, uri)
            self.tabs.setCurrentWidget(self.tree)  # Switch to Ontology Classes tab
        elif uri in self.property_uri_map.values():
            self.display_property_info(uri)
            self.expand_tree_item(self.object_properties_tree, uri)
            self.tabs.setCurrentWidget(self.object_properties_tree)  # Switch to Object Properties tab
        else:
            self.display_instance_info(uri)
            self.expand_tree_item(self.populated_tree, uri)
            self.tabs.setCurrentWidget(self.populated_tree)  # Switch to Populated Ontology tab
    
    def expand_tree_item(self, tree, uri):
        iterator = QTreeWidgetItemIterator(tree)
        while iterator.value():
            item = iterator.value()
            if item.text(0) == self.extract_last_part(uri):
                tree.setCurrentItem(item)
                item.setSelected(True)
                tree.scrollToItem(item)
                break
            iterator += 1
    
    def extract_last_part(self, uri):
        return uri.split('/')[-1].split('#')[-1]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OntologyViewer()
    window.show()
    sys.exit(app.exec_())