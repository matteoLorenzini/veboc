import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QTextBrowser, QSplitter, QTabWidget, QComboBox, QTreeWidgetItemIterator
from PyQt5.QtCore import Qt
import rdflib

class OntologyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ontology Viewer")
        
        self.upload_button = QPushButton("Upload Ontology")
        self.upload_button.clicked.connect(self.upload_ontology)
        
        self.preloaded_combo = QComboBox()
        self.preloaded_combo.addItem("Select Preloaded Ontology")
        self.preloaded_combo.activated[str].connect(self.load_preloaded_ontology)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Ontology Classes")
        self.tree.itemClicked.connect(self.on_class_item_clicked)
        
        self.object_properties_tree = QTreeWidget()
        self.object_properties_tree.setHeaderLabel("Object Properties")
        self.object_properties_tree.itemClicked.connect(self.on_property_item_clicked)
        
        self.info = QTextBrowser()
        self.info.setOpenExternalLinks(False)
        self.info.anchorClicked.connect(self.on_anchor_clicked)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tree, "Ontology Classes")
        self.tabs.addTab(self.object_properties_tree, "Object Properties")
        
        layout = QVBoxLayout()
        layout.addWidget(self.upload_button)
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
    
    def upload_ontology(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Ontology", "", "OWL files (*.owl);;RDF files (*.rdf)")
        if file_path:
            self.load_ontology(file_path)
            self.visualize_ontology()
            self.display_object_properties()
    
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
    
    def on_class_item_clicked(self, item, column):
        selected_class_short = item.text(column)
        print(f"Selected class short: {selected_class_short}")  # Debugging statement
        if selected_class_short in self.class_uri_map:
            selected_class = self.class_uri_map[selected_class_short]
            self.display_class_info(selected_class)
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
    
    def on_property_item_clicked(self, item, column):
        selected_property_short = item.text(column)
        print(f"Selected property short: {selected_property_short}")  # Debugging statement
        if selected_property_short in self.property_uri_map:
            selected_property = self.property_uri_map[selected_property_short]
            self.display_property_info(selected_property)
        else:
            print(f"Error: {selected_property_short} not found in property_uri_map")  # Debugging statement
    
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
    window = OntologyApp()
    window.show()
    sys.exit(app.exec_())