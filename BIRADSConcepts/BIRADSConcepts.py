import pandas as pd
import slicer
from slicer.ScriptedLoadableModule import *
import qSlicerSegmentationsModuleWidgetsPythonQt as SegWidgets
import vtkSegmentationCorePython as vtkSegCore
from slicer.util import VTKObservationMixin
import qt, ctk, vtk
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

        uiWidget = slicer.util.loadUI(self.resourcePath('UI/BIRADSConcepts.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        segmentEditorFrame = self.ui.segmentEditorFrame
        self.segmentEditorLayout = segmentEditorFrame.layout()
        self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorLayout.addWidget(self.segmentEditorWidget)

        self.logic = BIRADSConceptsLogic()
        self.controller = ReaderStudyController(self.ui, self.logic, self.segmentEditorWidget)
        self.controller.hideStudyWidgets()


class BIRADSConceptsLogic:
    def __init__(self):
        self.backend_directory = Path(__file__).parent.parent / "backend"
        self.reader_info_path = self.backend_directory / "info/reader_info.csv"
        self.examples_breast_dir = self.backend_directory / "data" / "examples_breast"
        self.info_csv_path = self.examples_breast_dir / "info_examples.csv"

        self.reader_df = pd.read_csv(self.reader_info_path)
        self.cases_df = pd.read_csv(self.info_csv_path, delimiter=';')

    def get_reader_cases(self, reader_name):
        reader_id = self.get_reader_id(reader_name)
        if reader_id is None:
            return None, None

        filtered = self.cases_df[self.cases_df['reader_ids'].astype(str).str.contains(str(reader_id))]
        cases = [g for _, g in filtered.groupby('study_id')]
        return reader_id, cases

    def get_reader_id(self, reader_name):
        match = self.reader_df[self.reader_df['reader_name'].str.lower() == reader_name.lower()]
        return match.iloc[0]['reader_id'] if not match.empty else None


class ReaderStudyController:
    def __init__(self, ui, logic: BIRADSConceptsLogic, segmentEditorWidget):
        self.ui = ui
        self.logic = logic
        self.caseList = []
        self.currentCaseIndex = -1
        self.massPresenceRight = None
        self.segmentEditorWidget = segmentEditorWidget

        self.ui.startStudyButton.connect('clicked(bool)', self.startStudy)
        self.ui.nextQuestionButton.connect('clicked(bool)', self.validateBiradsAndShowDensity)

        self.ui.biradsRight4.toggled.connect(lambda: self.ui.biradsRight4SubGroup.show() if self.ui.biradsRight4.isChecked() else self.ui.biradsRight4SubGroup.hide())
        self.ui.biradsLeft4.toggled.connect(lambda: self.ui.biradsLeft4SubGroup.show() if self.ui.biradsLeft4.isChecked() else self.ui.biradsLeft4SubGroup.hide())

        self.ui.massRightYes.toggled.connect(self.toggleMassSubmenus)
        self.ui.massRightNo.toggled.connect(self.toggleMassSubmenus)

        slicer.util.setDataProbeVisible(False)

    def hideStudyWidgets(self):
        self.ui.instructionLabel.hide()
        self.ui.biradsRightGroup.hide()
        self.ui.biradsLeftGroup.hide()
        self.ui.nextQuestionButton.hide()
        self.ui.densityRightGroup.hide()
        self.ui.densityLeftGroup.hide()
        self.ui.save_and_next.hide()
        self.ui.status_checked.hide()
        self.ui.biradsRight4SubGroup.hide()
        self.ui.biradsLeft4SubGroup.hide()
        self.ui.rightAssessmentLabel.hide()
        self.ui.rightMassGroup.hide()
        self.ui.rightMassShapeGroup.hide()
        self.ui.rightMassMarginGroup.hide()
        self.ui.rightMassDensityGroup.hide()
        self.ui.rightMassFeaturesGroup.hide()
        self.segmentEditorWidget.hide()

    def showBiradsSection(self):
        self.ui.instructionLabel.setText("Please, read this case and provide the BI-RADS score per breast.")
        self.ui.instructionLabel.show()
        self.ui.status_checked.show()
        self.ui.biradsRightGroup.show()
        self.ui.biradsLeftGroup.show()
        self.ui.nextQuestionButton.show()

    def validateBiradsAndShowDensity(self):
        self.ui.nextQuestionButton.show()  # Reuse this button for density transition
        self.ui.save_and_next.hide()       # Ensure Save and Next is hidden

        right_score = self.getSelectedButtonText(self.ui.biradsRightGroup)
        left_score = self.getSelectedButtonText(self.ui.biradsLeftGroup)

        if not right_score or not left_score:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select BI-RADS for both sides before continuing.")
            return
        if right_score == "BI-RADS 4" and not self.getSelectedButtonText(self.ui.biradsRight4SubGroup):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select BI-RADS 4 subcategory for the right breast.")
            return
        if left_score == "BI-RADS 4" and not self.getSelectedButtonText(self.ui.biradsLeft4SubGroup):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select BI-RADS 4 subcategory for the left breast.")
            return
        
        self.ui.nextQuestionButton.clicked.disconnect()  # Disconnect any previous connections
        self.ui.nextQuestionButton.connect('clicked(bool)', self.validateDensity)
        
        self.ui.nextQuestionButton.clicked.disconnect()
        self.ui.nextQuestionButton.clicked.connect(self.validateDensity)
        self.showDensitySection()

    def showDensitySection(self):
        self.ui.instructionLabel.setText("Please, assess the breast density per side.")
        self.ui.biradsRightGroup.hide()
        self.ui.biradsLeftGroup.hide()
        self.ui.biradsRight4SubGroup.hide()
        self.ui.biradsLeft4SubGroup.hide()

        self.ui.densityRightGroup.show()
        self.ui.densityLeftGroup.show()
        self.ui.nextQuestionButton.setText("Go to right breast assessment")
        self.ui.nextQuestionButton.show()
        self.ui.save_and_next.hide()

    def validateDensity(self):
        right_density = self.getSelectedButtonText(self.ui.densityRightGroup)
        left_density = self.getSelectedButtonText(self.ui.densityLeftGroup)

        if not right_density or not left_density:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select density for both sides before continuing.")
            return
        
        self.ui.nextQuestionButton.clicked.disconnect()
        self.ui.nextQuestionButton.clicked.connect(self.validateRightMass)

        self.showRightBreastAssessment()
    
    def showRightBreastAssessment(self):
        self.ui.instructionLabel.hide()
        self.ui.densityRightGroup.hide()
        self.ui.densityLeftGroup.hide()
        self.ui.rightAssessmentLabel.show()
        self.ui.rightMassGroup.show()

        self.ui.nextQuestionButton.setText("Next Question")
        self.ui.nextQuestionButton.clicked.disconnect()
        self.ui.nextQuestionButton.connect('clicked(bool)', self.validateRightMass)
    
    def validateRightMass(self):
        is_mass = self.getSelectedButtonText(self.ui.rightMassGroup)

        if not is_mass:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select Yes or No for mass presence.")
            return
        
        self.massPresenceRight = is_mass
        print(f"Mass presence (right breast): {self.massPresenceRight}")

        self.ui.rightMassGroup.hide()

        if is_mass.lower() == "yes":
            # Show submenus
            self.ui.rightMassShapeGroup.show()
            self.ui.rightMassMarginGroup.show()
            self.ui.rightMassDensityGroup.show()
            self.ui.rightMassFeaturesGroup.show()

            if not self.getSelectedButtonText(self.ui.rightMassShapeGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a mass shape.")
                return
            if not self.getSelectedButtonText(self.ui.rightMassMarginGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a mass margin.")
                return
            if not self.getSelectedButtonText(self.ui.rightMassDensityGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a mass density.")
                return

            # Validate associated features
            features = [
                self.ui.featureSkinRetraction, self.ui.featureNippleRetraction,
                self.ui.featureSkinThickening, self.ui.featureTrabecularThickening,
                self.ui.featureAxillaryAdenopathy, self.ui.featureArchitecturalDistortion,
                self.ui.featureCalcifications, self.ui.featureNone
            ]
            selected = [cb for cb in features if cb.isChecked()]
            if not selected:
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select at least one associated feature.")
                return
            if self.ui.featureNone.isChecked() and len(selected) > 1:
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Conflict", "'None of the above' cannot be selected with other options.")
                return


            self.ui.instructionLabel.setText(
                "Please segment the mass in the R-CC view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function."
            )
            self.ui.instructionLabel.show()
            self.launchSegmentEditorForRCC()
        else:
            pass
    
    def toggleMassSubmenus(self):
        is_yes = self.ui.massRightYes.isChecked()
        self.ui.rightMassShapeGroup.setVisible(is_yes)
        self.ui.rightMassMarginGroup.setVisible(is_yes)
        self.ui.rightMassDensityGroup.setVisible(is_yes)
        self.ui.rightMassFeaturesGroup.setVisible(is_yes)
    
    def launchSegmentEditorForRCC(self):
        # Retrieve RCC volume from the stored volume map
        try:
            rccNode = self.volume_map['RCC']
        except KeyError:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing RCC", "No RCC volume loaded.")
            return

        # Switch to a single slice view layout
        slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        slicer.util.setSliceViewerLayers(background=rccNode)

        # Get or create a Segment Editor node
        segmentEditorNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentEditorNode")
        if not segmentEditorNode:
            segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")

        # Create a new Segmentation Node
        segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        segmentationNode.SetName("RightBreastSegmentations")

        if not segmentationNode.GetDisplayNode():
            segmentationNode.CreateDefaultDisplayNodes()

        segmentation_mass = segmentationNode.GetSegmentation()
        massSegmentID = segmentation_mass.AddEmptySegment("Mass")

        # Use embedded widget (in the custom UI layout)
        self.segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        self.segmentEditorWidget.setSegmentationNode(segmentationNode)
        self.segmentEditorWidget.setSourceVolumeNode(rccNode)

        # Restrict visible tools to only the desired ones
        self.segmentEditorWidget.unorderedEffectsVisible = False
        self.segmentEditorWidget.setEffectNameOrder(["Threshold", "Paint", "Erase", "Smoothing"])

        # Activate the Threshold tool by default
        # self.segmentEditorWidget.setActiveEffectByName("Threshold")
        # Hide mass assessment submenus
        self.ui.rightAssessmentLabel.hide()
        self.ui.rightMassGroup.hide()
        self.ui.rightMassShapeGroup.hide()
        self.ui.rightMassMarginGroup.hide()
        self.ui.rightMassDensityGroup.hide()
        self.ui.rightMassFeaturesGroup.hide()

        self.segmentEditorWidget.show()
        self.ui.nextQuestionButton.setText("Save mass segmentation")
        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass
        self.ui.nextQuestionButton.clicked.connect(self.segmentMargins)

        if self.massPresenceRight.lower() == "yes":
            qt.QMessageBox.information(slicer.util.mainWindow(), "Segmentation required", "Please segment the mass in the R-CC view.")
    
    def segmentMargins(self):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if not segmentationNode:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Error", "No segmentation node found.")
            return

        massID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Mass")
        if self.isSegmentEmpty(segmentationNode, massID):
            qt.QMessageBox.warning(
                slicer.util.mainWindow(),
                "Empty Segment",
                "Mass segment is empty. Please complete the mass segmentation before proceeding."
            )
            return

        # Proceed to margins
        qt.QMessageBox.information(slicer.util.mainWindow(), "Next Segmentation", "Please segment the margins of the mass in the R-CC view.")
        self.ui.nextQuestionButton.setText("Save margins segmentation")
        self.ui.instructionLabel.setText("Please segment the margins of the mass in the R-CC view.\nTip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")

        rccNode = self.volume_map.get("RCC")
        if not rccNode:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing volume", "R-CC view not found.")
            return

        marginsSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("Margins")
        self.segmentEditorWidget.setCurrentSegmentID(marginsSegmentID)

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass
        # self.ui.nextQuestionButton.clicked.connect(self.finalizeMassSegmentation)

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
        self.ui.readerInputGroup.hide()
        self.loadNextCase()

    def loadNextCase(self):
        self.currentCaseIndex += 1
        if self.currentCaseIndex >= len(self.caseList):
            qt.QMessageBox.information(slicer.util.mainWindow(), "Done", "All cases reviewed.")
            return

        self.hideStudyWidgets()
        self.clearRadioSelections()

        case_df = self.caseList[self.currentCaseIndex]
        study_id = case_df.iloc[0]['study_id']
        case_folder = self.logic.examples_breast_dir / study_id
        slicer.mrmlScene.Clear(0)

        layout_map = {('R', 'CC'): 'RCC', ('R', 'MLO'): 'RMLO', ('L', 'CC'): 'LCC', ('L', 'MLO'): 'LMLO'}
        volume_map = {}
        for _, row in case_df.iterrows():
            tag = layout_map.get((row['laterality'], row['view_position']))
            dicom_file = case_folder / f"{row['image_id']}.dicom"
            if tag and dicom_file.exists():
                node = slicer.util.loadVolume(str(dicom_file))
                if node:
                    volume_map[tag] = node

        if len(volume_map) != 4:
            missing = set(layout_map.values()) - set(volume_map.keys())
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Load Error", f"Missing views: {', '.join(missing)} from {case_folder}")
            return

        self.setupLayout(volume_map)
        self.updateStatusLabel()
        self.showBiradsSection()
    
    def isSegmentEmpty(self, segmentationNode, segmentID):
        labelmap = vtkSegCore.vtkOrientedImageData()
        slicer.vtkSlicerSegmentationsModuleLogic.GetSegmentBinaryLabelmapRepresentation(
            segmentationNode, segmentID, labelmap
        )

        extent = labelmap.GetExtent()
        for z in range(extent[4], extent[5] + 1):
            for y in range(extent[2], extent[3] + 1):
                for x in range(extent[0], extent[1] + 1):
                    if labelmap.GetScalarComponentAsDouble(x, y, z, 0) != 0:
                        return False
        return True

    def clearRadioSelections(self):
        for group in [
            self.ui.biradsRightGroup, self.ui.biradsLeftGroup,
            self.ui.densityRightGroup, self.ui.densityLeftGroup,
            self.ui.biradsRight4SubGroup, self.ui.biradsLeft4SubGroup
        ]:
            for rb in group.findChildren(qt.QRadioButton):
                rb.setAutoExclusive(False)
                rb.setChecked(False)
                rb.setAutoExclusive(True)

    def getSelectedButtonText(self, groupBox):
        for button in groupBox.findChildren(qt.QRadioButton):
            if button.isChecked():
                return button.text
        return None
    
    def setupLayout(self, volume_map):
        self.volume_map = volume_map
        layout_id = 501
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
        layout_node = slicer.app.layoutManager().layoutLogic().GetLayoutNode()
        if not layout_node.GetLayoutDescription(layout_id):
            layout_node.AddLayoutDescription(layout_id, layout_xml)
        slicer.app.layoutManager().setLayout(layout_id)

        flipTags = ["RCC", "RMLO", "LCC", "LMLO"]

        for tag, node in volume_map.items():
            sliceNode = slicer.util.getNode(tag)
            logic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
            logic.GetSliceCompositeNode().SetBackgroundVolumeID(node.GetID())

            # Reset orientation to default
            sliceNode.SetOrientationToDefault()
            matrix = sliceNode.GetSliceToRAS()

            # Reset matrix to identity and flip X if needed
            for i in range(3):
                for j in range(3):
                    matrix.SetElement(i, j, 1.0 if i == j else 0.0)
            if tag in flipTags:
                matrix.SetElement(0, 0, -1.0)

            sliceNode.UpdateMatrices()

            # # Fit and zoom
            # sliceWidget = slicer.app.layoutManager().sliceWidget(tag)
            # logic = sliceWidget.sliceLogic()
            # logic.FitSliceToAll()

            # fov = sliceNode.GetFieldOfView()
            # zoomFactor = 0.75  # Zoom in by reducing FOV
            # sliceNode.SetFieldOfView(fov[0] * zoomFactor, fov[1] * zoomFactor, fov[2])
            sliceWidget = slicer.app.layoutManager().sliceWidget(tag)
            logic = sliceWidget.sliceLogic()
            sliceNode = logic.GetSliceNode()

            # Reset to default view
            logic.FitSliceToAll()

            # Apply controlled zoom (optional, e.g., zoom in by 15%)
            fov = sliceNode.GetFieldOfView()
            zoomFactor = 0.85
            sliceNode.SetFieldOfView(fov[0] * zoomFactor, fov[1] * zoomFactor, fov[2])

            # Recenter manually by resetting slice origin to center of image
            center = logic.GetSliceCompositeNode().GetBackgroundVolumeID()
            if center:
                bounds = [0] * 6
                slicer.util.getNode(center).GetRASBounds(bounds)
                centerX = (bounds[0] + bounds[1]) / 2.0
                centerY = (bounds[2] + bounds[3]) / 2.0
                centerZ = (bounds[4] + bounds[5]) / 2.0
                sliceNode.SetSliceOffset(centerZ)

    def updateStatusLabel(self):
        total = len(self.caseList)
        current = self.currentCaseIndex + 1
        self.ui.status_checked.setText(f"Cases read: {current} / {total}")
