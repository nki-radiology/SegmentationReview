import numpy as np
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

        self.ui.featureNone.toggled.connect(self.updateAssociatedFeatureSelections)
        for checkbox in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox):
            if checkbox != self.ui.featureNone:
                checkbox.toggled.connect(self.ensureNoneNotChecked)

        self.ui.calcificationsYes.toggled.connect(self.toggleCalcificationSubmenus)
        self.ui.calcificationsNo.toggled.connect(lambda: self.toggleCalcificationSubmenus(False))

        self.ui.morphologySuspicious.toggled.connect(self.toggleSuspiciousMorphologySubgroup)

        self.ui.asymmetryYes.toggled.connect(self.toggleAsymmetrySubtypes)
        self.ui.asymmetryNo.toggled.connect(lambda: self.toggleAsymmetrySubtypes(False))
        
        self.ui.architecturalDistortionNA.setEnabled(False)
        self.ui.massRightYes.toggled.connect(self.updateArchDistortionAvailability)
        self.ui.massRightNo.toggled.connect(self.updateArchDistortionAvailability)
        
        self.toggleCalcificationSubmenus(False) # Hide by default

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
        self.ui.asymmetryGroup.hide()
        self.ui.asymmetrySubtypeGroup.hide()
        self.ui.archDistortionGroup.hide()
        self.ui.calcificationsGroup.hide()
        self.ui.calcificationsMorphologyGroup.hide()
        self.ui.suspiciousMorphologySubGroup.hide()
        self.ui.calcificationsDistributionGroup.hide()
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
        self.ui.asymmetryGroup.show()
        self.ui.archDistortionGroup.show()
        self.ui.calcificationsGroup.show()

        self.ui.nextQuestionButton.setText("Next Question")
        self.ui.nextQuestionButton.clicked.disconnect()
        self.ui.nextQuestionButton.connect('clicked(bool)', self.validateRightMass)
    
    def validateRightMass(self):
        # --- MASS CHECK ---
        is_mass = self.getSelectedButtonText(self.ui.rightMassGroup)
        if not is_mass:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select Yes or No for mass presence.")
            return

        self.massPresenceRight = is_mass
        print(f"Mass presence (right breast): {self.massPresenceRight}")

        if is_mass.lower() == "yes":
            # Validate mass shape
            if not self.getSelectedButtonText(self.ui.rightMassShapeGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a mass shape.")
                return

            # Validate mass margin
            if not self.getSelectedButtonText(self.ui.rightMassMarginGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a mass margin.")
                return

            # Validate mass density
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

        # --- ASYMMETRY CHECK ---
        asymmetry = self.getSelectedButtonText(self.ui.asymmetryGroup)
        if not asymmetry:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please answer the asymmetry question.")
            return
        if asymmetry.lower() == "yes":
            subtype_selected = any(
                cb.isChecked() for cb in [
                    self.ui.asymmetryFocal,
                    self.ui.asymmetryGlobal,
                    self.ui.asymmetryDeveloping
                ]
            )
            if not subtype_selected:
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select at least one asymmetry type.")
                return

        # --- ARCHITECTURAL DISTORTION CHECK ---
        if not any(rb.isChecked() for rb in [self.ui.architecturalDistortionYes, self.ui.architecturalDistortionNo, self.ui.architecturalDistortionNA]):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please answer the architectural distortion question.")
            return

        # --- CALCIFICATIONS CHECK ---
        calcifications = self.getSelectedButtonText(self.ui.calcificationsGroup)
        if not calcifications:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please answer the calcifications question.")
            return

        if calcifications.lower() == "yes":
            # Morphology
            if not self.getSelectedButtonText(self.ui.calcificationsMorphologyGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a calcification morphology.")
                return

            # Distribution
            if not self.getSelectedButtonText(self.ui.calcificationsDistributionGroup):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select a calcification distribution.")
                return

        # All checks passed, proceed
        # self.ui.rightMassGroup.hide()
        # self.ui.rightMassShapeGroup.hide()
        # self.ui.rightMassMarginGroup.hide()
        # self.ui.rightMassDensityGroup.hide()
        # self.ui.rightMassFeaturesGroup.hide()
        # self.ui.asymmetryGroup.hide()
        # self.ui.asymmetrySubtypeGroup.hide()
        # self.ui.archDistortionGroup.hide()
        # self.ui.calcificationsGroup.hide()
        # self.ui.calcificationsMorphologyGroup.hide()
        # self.ui.suspiciousMorphologySubGroup.hide()
        # self.ui.calcificationsDistributionGroup.hide()

        # self.startRightBreastSegmentationSequence()
        self.promptQuestionLockConfirmation()
    
    def promptQuestionLockConfirmation(self):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Confirm Answers")
        msgBox.setText("Do you want to modify your answers?\nIf you press Continue, you will only be able to edit them at the end of the case.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
        msgBox.button(qt.QMessageBox.Ok).setText("Continue")
        msgBox.button(qt.QMessageBox.Cancel).setText("Edit answers")
        ret = msgBox.exec_()

        if ret == qt.QMessageBox.Ok:
            # self.lockQuestionInputs()
            # Hide the questions after confirmation
            self.ui.rightMassGroup.hide()
            self.ui.rightMassShapeGroup.hide()
            self.ui.rightMassMarginGroup.hide()
            self.ui.rightMassDensityGroup.hide()
            self.ui.rightMassFeaturesGroup.hide()
            self.ui.asymmetryGroup.hide()
            self.ui.asymmetrySubtypeGroup.hide()
            self.ui.archDistortionGroup.hide()
            self.ui.calcificationsGroup.hide()
            self.ui.calcificationsMorphologyGroup.hide()
            self.ui.suspiciousMorphologySubGroup.hide()
            self.ui.calcificationsDistributionGroup.hide()


            # Determine what to do based on the answers
            if self.ui.massRightYes.isChecked() or self.ui.asymmetryYes.isChecked() or \
            self.ui.calcificationsYes.isChecked() or self.ui.architecturalDistortionYes.isChecked():
                self.startRightBreastSegmentationSequence()
            else:
                pass
                # self.startLeftBreastAssessment()  # You will need to define this if not already
 
    def startRightBreastSegmentationSequence(self):
        self.segmentationQueue = []

        if self.ui.massRightYes.isChecked():
            self.segmentationQueue.append(self.segmentMassWithMarginsAndFeatures)
            if self.ui.asymmetryYes.isChecked():
                self.segmentationQueue.append(self.segmentAsymmetry)
                if self.ui.calcificationsYes.isChecked():
                    self.segmentationQueue.append(self.segmentCalcifications)
            else:
                if self.ui.calcificationsYes.isChecked():
                   self.segmentationQueue.append(self.segmentCalcifications)
        else:
            if self.ui.asymmetryYes.isChecked():
                self.segmentationQueue.append(self.segmentAsymmetry)
                if self.ui.architecturalDistortionYes.isChecked():
                    self.segmentationQueue.append(self.segmentDistortion)
                if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(self.segmentCalcifications) 
                else:
                   if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(self.segmentCalcifications)
            else:
                if self.ui.architecturalDistortionYes.isChecked():
                    self.segmentationQueue.append(self.segmentDistortion)
                if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(self.segmentCalcifications) 
                else:
                   if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(self.segmentCalcifications) 

        self.runNextSegmentationTask()

    def runNextSegmentationTask(self):
        if not self.segmentationQueue:
            self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
            self.promptRMLOSegmentation()
            try:
                self.ui.nextQuestionButton.clicked.disconnect()
            except TypeError:
                pass
            self.ui.nextQuestionButton.clicked.connect(self.promptRMLOSegmentation)
            return

        nextTask = self.segmentationQueue.pop(0)
        nextTask()

    def segmentMassWithMarginsAndFeatures(self):
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the mass in the R-CC view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.ui.nextQuestionButton.setText("Add next segment")
        self.launchSegmentEditor("RCC", "Mass")
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment the mass in the R-CC view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(self.validateMassSegmentation)

    def validateMassSegmentation(self):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        massID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Mass")
        if self.isSegmentEmpty(segmentationNode, massID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Mass segment is empty. Please complete it.")
            return
        

        self.segmentMargins()

    def segmentMargins(self):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment the margins of the mass in the R-CC view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        marginsSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("Margins")
        self.segmentEditorWidget.setCurrentSegmentID(marginsSegmentID)
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the margins of the mass in the R-CC view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")

        if not self.segmentationQueue:
            self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
        else:
            self.ui.nextQuestionButton.setText("Add next segment")

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(self.validateMarginsSegmentation)

    def validateMarginsSegmentation(self):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        marginsID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Margins")
        if self.isSegmentEmpty(segmentationNode, marginsID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Margins segment is empty. Please complete it.")
            return

        if any(cb.isChecked() for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox) if cb.text not in ["None of the above", "Axillary adenopathy"]):
            self.associatedFeaturesToSegment = self.getSelectedFeatures()
            self.currentFeatureIndex = 0
            self.segmentNextFeatureInQueue()
        else:
            self.runNextSegmentationTask()

    def segmentNextFeatureInQueue(self):
        if self.currentFeatureIndex >= len(self.associatedFeaturesToSegment):
            self.runNextSegmentationTask()
            return

        feature = self.associatedFeaturesToSegment[self.currentFeatureIndex]
        self.currentFeatureIndex += 1

        segmentationNode = self.segmentEditorWidget.segmentationNode()
        segmentID = segmentationNode.GetSegmentation().AddEmptySegment(feature)
        self.segmentEditorWidget.setCurrentSegmentID(segmentID)

        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment the {feature} in the R-CC view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the {feature} in the R-CC view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.ui.nextQuestionButton.setText("Add next segment")

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateFeatureSegmentation(segmentID, feature))

    def validateFeatureSegmentation(self, segmentID, feature):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", f"{feature} segment is empty. Please complete it.")
            return

        self.segmentNextFeatureInQueue()

    def segmentAsymmetry(self):
        self.startGenericSegmentation("Asymmetry")

    def segmentDistortion(self):
        self.startGenericSegmentation("MainDistortion")

    def segmentCalcifications(self):
        self.startGenericSegmentation("MainCalcifications")

    def startGenericSegmentation(self, name, view="RCC"):
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the {name} in the {view} view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        if len(self.segmentationQueue) == 0:
            self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
        else:
            self.ui.nextQuestionButton.setText("Add next segment")


        self.launchSegmentEditor("RCC", name)

        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment {name} in the {view} view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass
        
        print(f"SegmentID in startGenericSegmentation: {name}")
        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateGenericSegmentation(name))

    def validateGenericSegmentation(self, segmentID):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Segment is empty. Please complete it.")
            return

        if not self.segmentationQueue:
            self.promptRMLOSegmentation()
        else:
            self.runNextSegmentationTask()

    def promptRMLOSegmentation(self):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Continue to R-MLO?")
        msgBox.setText("Do you want to modify the segmentations?\nIf you press Continue, you will only be able to edit them at the end of the case.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
        msgBox.button(qt.QMessageBox.Ok).setText("Continue")
        msgBox.button(qt.QMessageBox.Cancel).setText("Edit segmentations")
        ret = msgBox.exec_()

        if ret == qt.QMessageBox.Ok:
            # self.startRMLOSegmentationSequence()
            pass 
    
    def toggleMassSubmenus(self):
        is_yes = self.ui.massRightYes.isChecked()
        self.ui.rightMassShapeGroup.setVisible(is_yes)
        self.ui.rightMassMarginGroup.setVisible(is_yes)
        self.ui.rightMassDensityGroup.setVisible(is_yes)
        self.ui.rightMassFeaturesGroup.setVisible(is_yes)
    
    def launchSegmentEditor(self, viewTag, initialSegmentName=None):
        self.ensureCustomLayoutAvailable()

        try:
            volNode = self.volume_map[viewTag]
            self.referenceVolumeNode = volNode
        except KeyError:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Missing {viewTag}", "No {viewTag} volume loaded.")
            return

        slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        slicer.util.setSliceViewerLayers(background=volNode)

        segmentEditorNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentEditorNode")
        if not segmentEditorNode:
            segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")

        segmentationNode = slicer.mrmlScene.GetFirstNodeByName("RightBreastSegmentations")
        if not segmentationNode:
            segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            segmentationNode.SetName("RightBreastSegmentations")
            segmentationNode.CreateDefaultDisplayNodes()

        self.segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        self.segmentEditorWidget.setSegmentationNode(segmentationNode)
        self.segmentEditorWidget.setSourceVolumeNode(volNode)

        self.segmentEditorWidget.unorderedEffectsVisible = False
        self.segmentEditorWidget.setEffectNameOrder(["Threshold", "Paint", "Erase", "Smoothing"])

        self.segmentEditorWidget.show()

        if initialSegmentName:
            segmentID = segmentationNode.GetSegmentation().AddEmptySegment(initialSegmentName)
            self.segmentEditorWidget.setCurrentSegmentID(segmentID)
    
    def updateAssociatedFeatureSelections(self):
        if self.ui.featureNone.isChecked():
            for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox):
                if cb != self.ui.featureNone:
                    cb.setChecked(False)

    def ensureNoneNotChecked(self):
        if any(cb.isChecked() for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox) if cb != self.ui.featureNone):
            self.ui.featureNone.setChecked(False)
    
    def updateArchDistortionAvailability(self):
        if self.ui.massRightYes.isChecked():
            self.ui.architecturalDistortionYes.setChecked(False)
            self.ui.architecturalDistortionNo.setChecked(False)
            self.ui.architecturalDistortionNA.setEnabled(True)
            self.ui.architecturalDistortionYes.setEnabled(False)
            self.ui.architecturalDistortionNo.setEnabled(False)
            self.ui.architecturalDistortionNA.setChecked(True)
        else:
            self.ui.architecturalDistortionNA.setChecked(False)
            self.ui.architecturalDistortionNA.setEnabled(False)
            self.ui.architecturalDistortionYes.setEnabled(True)
            self.ui.architecturalDistortionNo.setEnabled(True)

    def toggleCalcificationSubmenus(self, show=True):
        self.ui.calcificationsMorphologyGroup.setVisible(show)
        self.ui.calcificationsDistributionGroup.setVisible(show)
        if not show:
            self.ui.morphologySuspicious.setChecked(False)
            self.toggleSuspiciousMorphologySubgroup(False)

    def toggleSuspiciousMorphologySubgroup(self, show=True):
        self.ui.suspiciousMorphologySubGroup.setVisible(show)

    def toggleAsymmetrySubtypes(self, show=True):
        self.ui.asymmetrySubtypeGroup.setVisible(show)

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

        self.volume_map = volume_map
        qt.QTimer.singleShot(0, self.waitForSliceNodesAndSetupLayout)
        self.updateStatusLabel()
        self.showBiradsSection()
    
    def waitForSliceNodesAndSetupLayout(self):
        required_tags = ["RCC", "RMLO", "LCC", "LMLO"]
        layoutManager = slicer.app.layoutManager()

        self.ensureCustomLayoutAvailable()  # Register layout before use
        layoutManager.setLayout(501)

        def checkAndSetup():
            if all(slicer.util.getNodes(tag) for tag in required_tags):
                self.setupLayout(self.volume_map)
            else:
                qt.QTimer.singleShot(100, checkAndSetup)

        qt.QTimer.singleShot(100, checkAndSetup)

    def isSegmentEmpty(self, segmentationNode, segmentID, referenceVolumeNode):
        try:
            segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentID, referenceVolumeNode)
            return not np.any(segmentArray)
        except Exception as e:
            print(f"Error checking segment '{segmentID}': {e}")
            return True
    
    def getSelectedFeatures(self, include_axillary=False):
        features = []
        for checkbox in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox):
            if checkbox.isChecked() and checkbox.text != "None of the above":
                if include_axillary or checkbox.text != "Axillary adenopathy":
                    features.append(checkbox.text)
        return features
    
    def handleFeatureSegmentationStart(self):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        marginsID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("Margins")
        if self.isSegmentEmpty(segmentationNode, marginsID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Margins segment is empty. Please segment the margins.")
            return

        noneSelected = any(cb.text == "None of the above" and cb.isChecked() for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox))

        if noneSelected:
            pass

        self.associatedFeaturesToSegment = self.getSelectedFeatures()
        self.currentFeatureIndex = 0
        self.segmentNextFeature()

    def segmentNextFeature(self):
        if self.currentFeatureIndex >= len(self.associatedFeaturesToSegment):
            return

        feature = self.associatedFeaturesToSegment[self.currentFeatureIndex]
        self.currentFeatureIndex += 1

        qt.QMessageBox.information(slicer.util.mainWindow(), "Feature Segmentation", f"Please segment {feature} in the R-CC view.")

        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if not segmentationNode:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Error", "No segmentation node found.")
            return

        segmentID = segmentationNode.GetSegmentation().AddEmptySegment(feature)
        self.segmentEditorWidget.setCurrentSegmentID(segmentID)

        self.ui.instructionLabel.setText(f"Please segment the {feature} in the R-CC view.\nTip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.ui.nextQuestionButton.setText(f"Add next segment")

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(self.saveCurrentFeatureSegmentation)

    def saveCurrentFeatureSegmentation(self):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        feature = self.associatedFeaturesToSegment[self.currentFeatureIndex - 1]
        segmentID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(feature)
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"{feature} segment is empty. Please segment it before continuing.")
            return

        self.segmentNextFeature()

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
        self.ensureCustomLayoutAvailable()
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
        qt.QTimer.singleShot(0, lambda: slicer.app.layoutManager().setLayout(layout_id))


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
    
    def ensureCustomLayoutAvailable(self):
        layout_id = 501
        layout_xml = """<layout type="horizontal">
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
        </layout>"""
        layout_node = slicer.app.layoutManager().layoutLogic().GetLayoutNode()
        if not layout_node.GetLayoutDescription(layout_id):
            layout_node.AddLayoutDescription(layout_id, layout_xml)


    def updateStatusLabel(self):
        total = len(self.caseList)
        current = self.currentCaseIndex + 1
        self.ui.status_checked.setText(f"Cases read: {current} / {total}")
