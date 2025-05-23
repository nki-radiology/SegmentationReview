import pandas as pd
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import qt, ctk
from pathlib import Path


class BIRADSConcepts(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "BIRADSConcepts"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = []
        self.parent.helpText = """
        Module to review segmentations for assigned patients.
        """
        self.parent.acknowledgementText = """"""


class BIRADSConceptsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self.controller = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        slicer.util.setDataProbeVisible(False)

        # Load UI from file
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/BIRADSConcepts.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        self.logic = BIRADSConceptsLogic()
        self.controller = ReaderStudyController(self.ui, self.logic)


class BIRADSConceptsLogic:
    def __init__(self):
        self.backend_directory = Path(__file__).parent.parent / "backend"
        self.reader_info_path = self.backend_directory / "info/reader_info.csv"
        self.examples_breast_dir = self.backend_directory / "data" / "examples_breast"
        self.info_csv_path = self.examples_breast_dir / "info_examples.csv"

        self.reader_df = pd.read_csv(self.reader_info_path)
        # read with semicolon delimiter
        self.cases_df = pd.read_csv(self.info_csv_path, delimiter=';')

        self.cases_df = pd.read_csv(self.info_csv_path, delimiter=';')

    def get_reader_cases(self, reader_name):
        reader_id = self.get_reader_id(reader_name)
        if reader_id is None:
            return None, None

        filtered = self.cases_df[self.cases_df['reader_ids'].astype(str).str.contains(str(reader_id))]
        cases = [g for _, g in filtered.groupby('study_id')]
        print(f"{cases=}")
        return reader_id, cases

    def get_reader_id(self, reader_name):
        match = self.reader_df[
            self.reader_df['reader_name'].str.lower() == reader_name.lower()
        ]
        if not match.empty:
            return match.iloc[0]['reader_id']
        return None


class ReaderStudyController:
    def __init__(self, ui, logic: BIRADSConceptsLogic):
        self.ui = ui
        self.logic = logic
        self.caseList = []
        self.currentCaseIndex = -1

        self.ui.startStudyButton.connect('clicked(bool)', self.startStudy)
        self.ui.save_and_next.connect('clicked(bool)', self.loadNextCase)

        self.hideStudyWidgets()
        slicer.util.setDataProbeVisible(False)

    def hideStudyWidgets(self):
        self.ui.inputsCollapsibleButton.hide()
        self.ui.status_checked.hide()
        self.ui.overwrite_mask.hide()
        self.ui.save_and_next.hide()

    def showStudyWidgets(self):
        self.ui.inputsCollapsibleButton.show()
        self.ui.status_checked.show()
        self.ui.overwrite_mask.show()
        self.ui.save_and_next.show()

    def startStudy(self):
        name = self.ui.readerNameInput.text.strip()
        if not name:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing Input", "Please enter your name.")
            return

        reader_id, grouped_cases = self.logic.get_reader_cases(name)
        if reader_id is None or not grouped_cases:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Reader Not Found or No Cases", f"No reader ID or cases found for {name}.")
            return

        self.caseList = grouped_cases
        self.currentCaseIndex = -1
        self.showStudyWidgets()
        self.loadNextCase()

    def loadNextCase(self):
        self.currentCaseIndex += 1
        if self.currentCaseIndex >= len(self.caseList):
            qt.QMessageBox.information(slicer.util.mainWindow(), "Done", "All cases reviewed.")
            return

        case_df = self.caseList[self.currentCaseIndex]
        study_id = case_df.iloc[0]['study_id']
        case_folder = self.logic.examples_breast_dir / study_id

        slicer.mrmlScene.Clear(0)

        # Expected views
        layout_map = {
            ('R', 'CC'): 'RCC',
            ('R', 'MLO'): 'RMLO',
            ('L', 'CC'): 'LCC',
            ('L', 'MLO'): 'LMLO'
        }

        volume_map = {}
        for _, row in case_df.iterrows():
            lat = row['laterality']
            view = row['view_position']
            tag = layout_map.get((lat, view))
            if not tag:
                continue
            dicom_file = case_folder / f"{row['image_id']}.dicom"
            print(f"{dicom_file=}")
            if dicom_file.exists():
                success, node = slicer.util.loadVolume(str(dicom_file), returnNode=True)
                if success:
                    volume_map[tag] = node

        if len(volume_map) != 4:
            missing = set(layout_map.values()) - set(volume_map.keys())
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Load Error", f"Missing views: {', '.join(missing)} from {case_folder}")
            return

        self.setupLayout(volume_map)
        self.updateStatusLabel()


    def setupLayout(self, volume_map):
        layout_xml = """
        <layout type="horizontal">
        <item>
            <layout type="vertical">
            <item><view class="vtkMRMLSliceNode" singletontag="RCC"/></item>
            <item><view class="vtkMRMLSliceNode" singletontag="RMLO"/></item>
            </layout>
        </item>
        <item>
            <layout type="vertical">
            <item><view class="vtkMRMLSliceNode" singletontag="LCC"/></item>
            <item><view class="vtkMRMLSliceNode" singletontag="LMLO"/></item>
            </layout>
        </item>
        </layout>
        """
        layout_id = 501
        layout_node = slicer.app.layoutManager().layoutLogic().GetLayoutNode()
        if not layout_node.GetLayoutDescription(layout_id):
            layout_node.AddLayoutDescription(layout_id, layout_xml)
        slicer.app.layoutManager().setLayout(layout_id)

        for tag, node in volume_map.items():
            sliceNode = slicer.util.getNode(tag)
            logic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
            logic.GetSliceCompositeNode().SetBackgroundVolumeID(node.GetID())

    def updateStatusLabel(self):
        total = len(self.caseList)
        current = self.currentCaseIndex + 1
        self.ui.status_checked.setText(f"Checked: {current} / {total}")
