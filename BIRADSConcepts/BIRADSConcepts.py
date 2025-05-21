import pandas as pd
import os
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
        self.reader_id = None
        self.assigned_patients = []
        
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        slicer.util.setDataProbeVisible(False)


        # Load UI from file
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/BIRADSConcepts.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Initially hide all other widgets
        self.ui.status_checked.hide()
        self.ui.inputsCollapsibleButton.hide()
        self.ui.save_and_next.hide()
        self.ui.overwrite_mask.hide()


        self.logic = BIRADSConceptsLogic()

        # Connect signals to slots
        self.ui.startStudyButton.connect('clicked(bool)', self.onStartStudy)

        # self.layout.addStretch(1)
    
    def onStartStudy(self):
        reader_name = self.ui.readerNameInput.text.strip()
        if not reader_name:
            qt.QMessageBox.warning(None, "Input Error", "Please enter your name.")
            return
        
        # Load reader info
        
        self.reader_id = self.logic.get_reader_id(reader_name=reader_name)
        if self.reader_id is None:
            qt.QMessageBox.warning(None, "Reader Not Found", f"No reader ID found for {reader_name}.")
            return
        
        # Load assigned patients
        self.assigned_patients = self.logic.get_patients_for_reader(reader_id=self.reader_id)
        if not self.assigned_patients:
            qt.QMessageBox.information(None, "No Cases", "No cases assigned to this reader.")
        else:
            qt.QMessageBox.information(None, "Case Loaded", f"Cases: {','.join(self.assigned_patients)}")




    # def onLoadAssignedPatients(self):
    #     reader_name = self.readerNameInput.text.strip()
    #     if not reader_name:
    #         self.statusLabel.setText("Please enter a reader name.")
    #         return

    #     reader_id = self.logic.get_reader_id(reader_name)
    #     if reader_id is None:
    #         self.statusLabel.setText("Reader name not found.")
    #         return

    #     self.reader_id = reader_id
    #     self.assigned_patients = self.logic.get_patients_for_reader(reader_id)

    #     self.statusLabel.setText(f"Loaded {len(self.assigned_patients)} patients for reader ID {reader_id}.")


class BIRADSConceptsLogic:
    def __init__(self):
        # Paths to CSVs 
        self.backend_directory = Path(__file__).parent.parent / "backend"
        self.reader_info_path = self.backend_directory / "info/reader_info.csv"
        self.assignment_path = self.backend_directory / "info/patient_assignment.csv"

        self.reader_df = pd.read_csv(self.reader_info_path)
        self.assignment_df = pd.read_csv(self.assignment_path)

    def get_reader_id(self, reader_name):
        match = self.reader_df[self.reader_df['reader_name'].str.lower() == reader_name.lower()]
        if not match.empty:
            return match.iloc[0]['reader_id']
        return None

    def get_patients_for_reader(self, reader_id):
        patients = self.assignment_df[self.assignment_df['reader_ids'].astype(str).str.contains(str(reader_id))]
        return patients['patient_id'].tolist()
