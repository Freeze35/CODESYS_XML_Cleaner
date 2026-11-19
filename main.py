import sys
import os
import re
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.setText("Перетащите сюда XML файл\nили нажмите для выбора")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #8f8f8f;
                border-radius: 8px;
                padding: 20px;
                background-color: #fafafa;
                font-size: 14px;
                color: #333;
            }
            QLabel:hover {
                border-color: #0078d7;
                background-color: #f0f7ff;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith('.xml'):
                self.set_file(path)
            else:
                QMessageBox.warning(self.window(), "Предупреждение", "Поддерживаются только XML файлы.")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self.window(),
                "Выберите XML файл",
                "",
                "XML Files (*.xml)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            if path:
                self.set_file(path)

    def set_file(self, path):
        self.file_path = path
        self.setText(f"Выбран файл:\n{os.path.basename(path)}")


class XMLProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CODESYS SymbolConfig Clean Tool")
        self.resize(520, 260)
        self.save_path = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.drop_area = DropLabel()
        layout.addWidget(self.drop_area)

        save_layout = QHBoxLayout()
        self.lbl_save_path = QLabel("Путь сохранения: не выбран")
        self.lbl_save_path.setWordWrap(True)
        self.btn_select_save = QPushButton("Сохранить как...")
        self.btn_select_save.clicked.connect(self.select_save_path)

        save_layout.addWidget(self.lbl_save_path, stretch=1)
        save_layout.addWidget(self.btn_select_save)
        layout.addLayout(save_layout)

        self.btn_execute = QPushButton("Конвертировать XML")
        self.btn_execute.setFixedHeight(40)
        self.btn_execute.setStyleSheet("""
            QPushButton {
                font-weight: bold; 
                background-color: #0078d7; 
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.btn_execute.clicked.connect(self.run_processing)
        layout.addWidget(self.btn_execute)

    def select_save_path(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Укажите место сохранения",
            "",
            "XML Files (*.xml)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if path:
            if not path.lower().endswith('.xml'):
                path += '.xml'
            self.save_path = path
            self.lbl_save_path.setText(f"Путь: {path}")

    def process_xml(self, input_file, output_file):
        """Удаляет лишние Attribute, сохраняя qualified_only, и делает пустые Node самозакрывающимися."""
        ET.register_namespace('', "http://3s-software.com")

        tree = ET.parse(input_file)
        root = tree.getroot()

        for node in root.findall('.//{*}Node'):
            for child in list(node):
                if child.tag.endswith('Attribute'):
                    attr_text = child.text or ""
                    if not attr_text.startswith("qualified_only"):
                        node.remove(child)

            if len(node) == 0:
                node.text = None

        ET.indent(tree, space="  ")

        xml_str = ET.tostring(root, encoding='unicode')
        xml_str = re.sub(r'(?<! )/>>', ' />', xml_str)

        full_xml = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_str

        with open(output_file, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(full_xml)

    def run_processing(self):
        if not self.drop_area.file_path or not os.path.exists(self.drop_area.file_path):
            QMessageBox.warning(self, "Ошибка выполнения", "Исходный файл не указан!")
            return

        if not self.save_path:
            QMessageBox.warning(self, "Ошибка выполнения", "Укажите путь для сохранения файла!")
            return

        try:
            self.process_xml(self.drop_area.file_path, self.save_path)
            QMessageBox.information(self, "Успех", f"Файл успешно преобразован:\n{self.save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка обработки", f"Произошла ошибка:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = XMLProcessorApp()
    window.show()
    sys.exit(app.exec())
