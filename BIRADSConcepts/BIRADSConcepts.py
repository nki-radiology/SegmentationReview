import numpy as np
import pandas as pd
import slicer
from slicer.ScriptedLoadableModule import *
import qSlicerSegmentationsModuleWidgetsPythonQt as SegWidgets
import vtkSegmentationCorePython as vtkSegCore
import vtkSegmentationCorePython as vtkSeg
from slicer.util import VTKObservationMixin
import qt, ctk, vtk
# from __main__ import qt
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

class TemporaryInstructionFrame(qt.QFrame):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(qt.Qt.ToolTip | qt.Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #a9a9a9;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                font-size: 12pt;
                color: black;
            }
        """)

        layout = qt.QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 8, 12, 8)

        # Warning icon
        iconLabel = qt.QLabel()
        icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxWarning)
        iconLabel.setPixmap(icon.pixmap(32, 32))
        layout.addWidget(iconLabel)

        # Message label
        messageLabel = qt.QLabel(message)
        messageLabel.setWordWrap(True)
        layout.addWidget(messageLabel)

        self.setLayout(layout)


# class ClickFilter(qt.QObject):
#     def __init__(self, target):
#         super().__init__()
#         self.target = target

#     def eventFilter(self, obj, event):
#         if event.type() == qt.QEvent.MouseButtonPress:
#             self.target.close()
#             slicer.util.mainWindow().removeEventFilter(self)
#         return False

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
                self.runRCCSegmentation()
            else:
                pass
                # self.startLeftBreastAssessment()  # You will need to define this if not already
 
    def startRightBreastSegmentationSequence(self, viewTag):
        self.segmentationQueue = []

        if self.ui.massRightYes.isChecked():
            print(f"I'm before self.segmentationQueue.append(Mass), {viewTag}")
            self.segmentationQueue.append(lambda: self.segmentMass(viewTag))
            if self.ui.asymmetryYes.isChecked():
                self.segmentationQueue.append(lambda: self.segmentAsymmetry(viewTag))
                if self.ui.calcificationsYes.isChecked():
                    self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag))
            else:
                if self.ui.calcificationsYes.isChecked():
                   self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag))
        else:
            if self.ui.asymmetryYes.isChecked():
                self.segmentationQueue.append(lambda: self.segmentAsymmetry(viewTag))
                if self.ui.architecturalDistortionYes.isChecked():
                    self.segmentationQueue.append(lambda: self.segmentDistortion(viewTag))
                if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag)) 
                else:
                   if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag))
            else:
                if self.ui.architecturalDistortionYes.isChecked():
                    self.segmentationQueue.append(lambda: self.segmentDistortion(viewTag))
                if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag)) 
                else:
                   if self.ui.calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag)) 
        self.runNextSegmentationTask(viewTag)
    
    def runRCCSegmentation(self):
        self.startRightBreastSegmentationSequence("RCC")
    
    def runRMLOSegmentation(self):
        rccSegNode = slicer.mrmlScene.GetFirstNodeByName("RCC-Segmentations")
        if rccSegNode:
            displayNode = rccSegNode.GetDisplayNode()
            if displayNode:
                displayNode.SetVisibility(False)

        self.startRightBreastSegmentationSequence("RMLO")

    def runNextSegmentationTask(self, viewTag):
        if not self.segmentationQueue:
            if viewTag=="RCC":
                self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
                try:
                    self.ui.nextQuestionButton.clicked.disconnect()
                except TypeError:
                    pass
                self.ui.nextQuestionButton.clicked.connect(self.promptRMLOSegmentation)
                return
            elif viewTag=="RMLO":
                self.ui.nextQuestionButton.setText("Continue to left breast assessment")
                try:
                    self.ui.nextQuestionButton.clicked.disconnect()
                except TypeError:
                    pass
                return

        nextTask = self.segmentationQueue.pop(0)
        nextTask()

    def segmentMass(self, viewTag):
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the mass in the {viewTag} view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.ui.nextQuestionButton.setText("Add next segment")
        self.launchSegmentEditor(viewTag, f"{viewTag}-Mass")
        # msgBox = qt.QMessageBox(slicer.util.mainWindow())
        # msgBox.setWindowTitle("Segmentation Instruction")
        # msgBox.setText(f"Please segment the mass in the {viewTag} view.")
        # msgBox.setStandardButtons(qt.QMessageBox.Ok)
        # msgBox.exec_()
        self.showTemporaryInstruction(f"Please segment the mass in the {viewTag} view.")

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateMassSegmentation(viewTag))

    def validateMassSegmentation(self, viewTag):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        massID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(f"{viewTag}-Mass")
        if self.isSegmentEmpty(segmentationNode, massID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Mass segment is empty. Please complete it.")
            return

        self.segmentationQueue.insert(0, lambda: self.segmentMargins(viewTag))
        self.runNextSegmentationTask(viewTag)
    
    def segmentMargins(self, viewTag):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment the margins of the mass in the {viewTag} view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()

        segmentationNode = self.segmentEditorWidget.segmentationNode()
        segmentName = f"{viewTag}-Margins"
        existingID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segmentName)
        if existingID:
            marginsSegmentID = existingID
        else:
            marginsSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(segmentName)
        self.segmentEditorWidget.setCurrentSegmentID(marginsSegmentID)

        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the margins of the mass in the {viewTag} view.\n"
                                        "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.associatedFeaturesToSegment = self.getSelectedFeatures(viewTag)
        noMoreTasks = not self.segmentationQueue and len(self.associatedFeaturesToSegment)==0
        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateMarginsSegmentation(viewTag, noMoreTasks))
        if noMoreTasks:
            self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation" if viewTag=="RCC" else "Continue to left breast assessment")
        else:
            self.ui.nextQuestionButton.setText("Add next segment")
            
    
    def validateMarginsSegmentation(self, viewTag, noMoreTasksAfterMargins):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        marginsID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(f"{viewTag}-Margins")
        if self.isSegmentEmpty(segmentationNode, marginsID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Margins segment is empty. Please complete it.")
            return
        
        if not noMoreTasksAfterMargins:
            if viewTag == "RCC":
                if any(cb.isChecked() for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox) if cb.text not in ["None of the above", "Axillary adenopathy"]):
                    self.currentFeatureIndex = 0
                    self.segmentNextFeatureInQueue(viewTag)
                else:
                    self.runNextSegmentationTask(viewTag)
            elif viewTag == "RMLO":
                print(f"I am in the if RMLO in validateMarginsSegmentation in {viewTag}")
                if any(cb.isChecked() for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox) if cb.text != "None of the above"):
                    self.currentFeatureIndex = 0
                    self.segmentNextFeatureInQueue(viewTag)
                else:
                    self.runNextSegmentationTask(viewTag)
        else:
            if viewTag=="RCC":
                self.promptRMLOSegmentation()
            elif viewTag=="RMLO":
                pass
            # self.runNextSegmentationTask(viewTag)


    def segmentNextFeatureInQueue(self, viewTag):
        if self.currentFeatureIndex >= len(self.associatedFeaturesToSegment):
            self.runNextSegmentationTask(viewTag)
            return

        feature = self.associatedFeaturesToSegment[self.currentFeatureIndex]
        self.currentFeatureIndex += 1

        segmentationNode = self.segmentEditorWidget.segmentationNode()
        segmentID = segmentationNode.GetSegmentation().AddEmptySegment(f"{viewTag}-{feature}")
        self.segmentEditorWidget.setCurrentSegmentID(segmentID)

        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment the {feature} in the {viewTag} view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the {feature} in the {viewTag} view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        noMoreTasks = not self.segmentationQueue and self.currentFeatureIndex==len(self.associatedFeaturesToSegment)
        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass
        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateFeatureSegmentation(segmentID, feature, viewTag, noMoreTasks))
        if noMoreTasks:
            self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation" if viewTag=="RCC" else "Continue to left breast assessment")
        else:
            self.ui.nextQuestionButton.setText("Add next segment")

    def validateFeatureSegmentation(self, segmentID, feature, viewTag, noMoreTasksAfterFeatures):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", f"{feature} segment is empty. Please complete it.")
            return
        if not noMoreTasksAfterFeatures:
            self.segmentNextFeatureInQueue(viewTag)
        else:
            if viewTag=="RCC":
                self.promptRMLOSegmentation()
            elif viewTag=="RMLO":
                pass

    def segmentAsymmetry(self, viewTag):
        self.startGenericSegmentation(f"{viewTag}-Asymmetry", viewTag)

    def segmentDistortion(self, viewTag):
        self.startGenericSegmentation(f"{viewTag}-MainDistortion", viewTag)

    def segmentCalcifications(self, viewTag):
        self.startGenericSegmentation(f"{viewTag}-MainCalcifications", viewTag)

    def startGenericSegmentation(self, name, viewTag):
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the {name} in the {viewTag} view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        if len(self.segmentationQueue) == 0 and viewTag=="RCC":
            self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
        elif len(self.segmentationQueue) == 0 and viewTag=="RMLO":
            self.ui.nextQuestionButton.setText("Continue to left breast assessment") 
        else:
            self.ui.nextQuestionButton.setText("Add next segment")

        self.launchSegmentEditor(viewTag, name)

        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment {name} in the {viewTag} view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()

        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateGenericSegmentation(name, viewTag))

    def validateGenericSegmentation(self, segmentID, viewTag):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", f"{segmentID} is empty. Please complete it.")
            return

        if not self.segmentationQueue:
            self.promptRMLOSegmentation()
        else:
            self.runNextSegmentationTask(viewTag)

    def promptRMLOSegmentation(self):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Continue to R-MLO?")
        msgBox.setText("Do you want to modify the segmentations?\nIf you press Continue, you will only be able to edit them at the end of the case.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
        msgBox.button(qt.QMessageBox.Ok).setText("Continue")
        msgBox.button(qt.QMessageBox.Cancel).setText("Edit segmentations")
        ret = msgBox.exec_()

        if ret == qt.QMessageBox.Ok:
            self.runRMLOSegmentation()
    
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

        segmentationNode = slicer.mrmlScene.GetFirstNodeByName(f"{viewTag}-Segmentations")
        if not segmentationNode:
            segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            segmentationNode.SetName(f"{viewTag}-Segmentations")
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
                if cb != self.ui.featureNone and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)

    def ensureNoneNotChecked(self):
        if any(cb.isChecked() for cb in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox) if cb != self.ui.featureNone):
            self.ui.featureNone.blockSignals(True)
            self.ui.featureNone.setChecked(False)
            self.ui.featureNone.blockSignals(False)

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
    
    def getSelectedFeatures(self, viewTag):
        features = []
        if viewTag=="RCC":
            for checkbox in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox):
                if checkbox.isChecked() and checkbox.text != "None of the above" and checkbox.text != "Axillary adenopathy":
                    features.append(checkbox.text)
        elif viewTag=="RMLO":
            for checkbox in self.ui.rightMassFeaturesGroup.findChildren(qt.QCheckBox):
                if checkbox.isChecked() and checkbox.text != "None of the above":
                    features.append(checkbox.text) 
        return features
    
    def segmentNextFeature(self, viewTag):
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

        self.ui.nextQuestionButton.clicked.connect(lambda: self.saveCurrentFeatureSegmentation(viewTag))

    def saveCurrentFeatureSegmentation(self, viewTag):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        feature = self.associatedFeaturesToSegment[self.currentFeatureIndex - 1]
        segmentID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(feature)
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"{feature} segment is empty. Please segment it before continuing.")
            return

        self.segmentNextFeature(viewTag)

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
        
    # def showTemporaryInstruction(self, message):
    #     if hasattr(self, "temporaryInstructionDialog"):
    #         self.temporaryInstructionDialog.close()

    #     dlg = qt.QDialog(slicer.util.mainWindow())
    #     dlg.setWindowFlags(qt.Qt.FramelessWindowHint | qt.Qt.Dialog)
    #     dlg.setModal(False)
    #     # dlg.setAttribute(qt.Qt.WA_TranslucentBackground)
    #     dlg.setStyleSheet("""
    #         QDialog {
    #             background-color: #f0f0f0;
    #             border: 1px solid gray;
    #             border-radius: 10px;
    #         }
    #         QLabel#titleLabel {
    #             font-weight: bold;
    #             font-size: 15pt;
    #             qproperty-alignment: AlignCenter;
    #         }
    #         QLabel#messageLabel {
    #             font-weight: bold:
    #             font-size: 15pt;
    #             qproperty-alignment: AlignCenter;
    #         }
    #         QFrame#line {
    #             background-color: gray;
    #             max-height: 1px;
    #             min-height: 1px;
    #         }
    #     """)

    #     layout = qt.QVBoxLayout()
    #     dlg.setLayout(layout)

    #     titleLabel = qt.QLabel("Segmentation Instruction")
    #     titleLabel.setObjectName("titleLabel")
    #     layout.addWidget(titleLabel)

    #     line = qt.QFrame()
    #     line.setFrameShape(qt.QFrame.HLine)
    #     line.setObjectName("line")
    #     layout.addWidget(line)

    #     messageLabel = qt.QLabel(message)
    #     messageLabel.setObjectName("messageLabel")
    #     layout.addWidget(messageLabel)

    #     dlg.adjustSize()
    # # Position in the center of the main window (no decorations)
    #     mainWindow = slicer.util.mainWindow()
    #     mainRect = mainWindow.geometry

    #     centerX = mainRect.left() + mainRect.width() // 2
    #     centerY = mainRect.top() + mainRect.height() // 2

    #     dlg.move(
    #         centerX - dlg.width // 2,
    #         centerY - dlg.height // 2
    #     )

    #     self.temporaryInstructionDialog = dlg
    #     dlg.show()

    #     # Auto-close on any click in the main window
    #     class ClickFilter(qt.QObject):
    #         def eventFilter(filterSelf, obj, event):
    #             if event.type() == qt.QEvent.MouseButtonPress:
    #                 dlg.close()
    #                 slicer.util.mainWindow().removeEventFilter(filterSelf)
    #             return False

    #     self.clickFilter = ClickFilter()
    #     slicer.util.mainWindow().installEventFilter(self.clickFilter)


    # def showTemporaryInstruction(self, text):
    #     if hasattr(self, "temporaryInstructionDialog") and self.temporaryInstructionDialog:
    #         self.temporaryInstructionDialog.close()

    #     self.temporaryInstructionDialog = qt.QDialog(slicer.util.mainWindow())
    #     self.temporaryInstructionDialog.setWindowFlags(
    #         qt.Qt.FramelessWindowHint | qt.Qt.Dialog)
    #     self.temporaryInstructionDialog.setAttribute(qt.Qt.WA_TranslucentBackground)
    #     self.temporaryInstructionDialog.setModal(False)

    #     mainLayout = qt.QVBoxLayout(self.temporaryInstructionDialog)
    #     mainLayout.setContentsMargins(0, 0, 0, 0)

    #     frame = qt.QFrame()
    #     frame.setFrameShape(qt.QFrame.Box)
    #     frame.setStyleSheet("""
    #         QFrame {
    #             background-color: #f0f0f0;
    #             border: 1px solid gray;
    #             border-radius: 10px;
    #         }
    #     """)
    #     layout = qt.QVBoxLayout(frame)
    #     layout.setContentsMargins(20, 20, 20, 20)
    #     layout.setSpacing(15)

    #     # Title label
    #     titleLabel = qt.QLabel("Segmentation Instruction")
    #     titleLabel.setStyleSheet("font-weight: bold; font-size: 16pt;")
    #     layout.addWidget(titleLabel)

    #     # Body text
    #     textLabel = qt.QLabel(text)
    #     textLabel.setStyleSheet("font-size: 12pt;")
    #     textLabel.setWordWrap(True)
    #     layout.addWidget(textLabel)

    #     mainLayout.addWidget(frame)

    #     # Size and position
    #     self.temporaryInstructionDialog.setMinimumWidth(500)
    #     self.temporaryInstructionDialog.setMinimumHeight(180)

    #     # Get main window geometry
    #     mainWindow = slicer.util.mainWindow()
    #     mainRect = mainWindow.geometry  # NOT .frameGeometry, to avoid decorations

    #     # Compute center
    #     centerX = mainRect.left() + mainRect.width() // 2
    #     centerY = mainRect.top() + mainRect.height() // 2

    #     # Move dialog
    #     self.temporaryInstructionDialog.move(
    #         centerX - self.temporaryInstructionDialog.width // 2,
    #         centerY - self.temporaryInstructionDialog.height // 2
    #     )

    #     class ClickFilter(qt.QObject):
    #         def __init__(self, dialog):
    #             super().__init__()
    #             self.dialog = dialog

    #         def eventFilter(self, obj, event):
    #             if event.type() in [qt.QEvent.MouseButtonPress, qt.QEvent.KeyPress]:
    #                 self.dialog.close()
    #                 slicer.util.mainWindow().removeEventFilter(self)
    #             return False

    #     self.clickFilter = ClickFilter(self.temporaryInstructionDialog)
    #     slicer.util.mainWindow().installEventFilter(self.clickFilter)

    #     self.temporaryInstructionDialog.show()


    # def showTemporaryInstruction(self, message):
    #     if hasattr(self, "temporaryInstructionFrame"):
    #         self.temporaryInstructionFrame.close()

    #     self.temporaryInstructionFrame = TemporaryInstructionFrame(message, slicer.util.mainWindow())
    #     self.temporaryInstructionFrame.adjustSize()

    #     # Center in main window
    #     mw = slicer.util.mainWindow().geometry
    #     fw = self.temporaryInstructionFrame.frameGeometry
    #     x = mw.center().x() - fw.width() // 2
    #     y = mw.center().y() - fw.height() // 2
    #     self.temporaryInstructionFrame.move(x, y)
    #     self.temporaryInstructionFrame.show()

    #     # Install dismiss-on-click filter
    #     self.clickFilter = ClickFilter(self.temporaryInstructionFrame)
    #     slicer.util.mainWindow().installEventFilter(self.clickFilter)


    
    def showTemporaryInstruction(self, text):
        if hasattr(self, 'temporaryWarningFrame') and self.temporaryInstructionFrame:
            self.temporaryInstructionFrame.deleteLater()

        parent = slicer.util.mainWindow()

        # Create a QFrame container
        self.temporaryInstructionFrame = qt.QFrame(parent)
        self.temporaryInstructionFrame.setFrameShape(qt.QFrame.StyledPanel)
        self.temporaryInstructionFrame.setFrameShadow(qt.QFrame.Raised)
        self.temporaryInstructionFrame.setStyleSheet("""
            QFrame {
                background-color: #fefefe;
                border: 2px solid #f1c40f;
                border-radius: 10px;
            }
            QLabel {
                color: black;
                padding: 10px;
                font-size: 13pt;
            }
        """)

        # Add an icon and message
        layout = qt.QHBoxLayout(self.temporaryInstructionFrame)
        iconLabel = qt.QLabel()
        icon = qt.QApplication.style().standardIcon(qt.QStyle.SP_MessageBoxWarning)
        iconLabel.setPixmap(icon.pixmap(32, 32))

        textLabel = qt.QLabel(text)
        textLabel.setWordWrap(True)

        layout.addWidget(iconLabel)
        layout.addWidget(textLabel)

        self.temporaryInstructionFrame.adjustSize()

        # Center it over the Slicer window
        # mw = parent.geometry
        # fw = self.temporaryInstructionFrame.frameGeometry()
        # x = mw().center().x() - fw.width() // 2
        # y = mw().center().y() - fw.height() // 2
        # self.temporaryInstructionFrame.move(x, y)
        mw = parent.geometry
        fw = self.temporaryInstructionFrame.frameGeometry
        x = mw.center().x() - fw.width() // 2
        y = mw.center().y() - fw.height() // 2
        self.temporaryInstructionFrame.move(x,y)

        self.temporaryInstructionFrame.setWindowFlags(qt.Qt.ToolTip)
        self.temporaryInstructionFrame.show()

        # Hide on any click
        class ClickFilter(qt.QObject):
            def __init__(self, frame):
                super().__init__()
                self.frame = frame

            def eventFilter(self, obj, event):
                if event.type() == qt.QEvent.MouseButtonPress:
                    self.frame.hide()
                    self.frame.deleteLater()
                    slicer.util.mainWindow().removeEventFilter(self)
                    return True
                return False

        self.clickFilter = ClickFilter(self.temporaryInstructionFrame)
        slicer.util.mainWindow().installEventFilter(self.clickFilter)


    # def showTemporaryInstruction(self, text):
    #     if hasattr(self, 'temporaryOverlayLabel') and self.temporaryOverlayLabel:
    #         self.temporaryOverlayLabel.deleteLater()

    #     self.temporaryOverlayLabel = qt.QLabel(slicer.util.mainWindow())
    #     self.temporaryOverlayLabel.setText(text)
    #     self.temporaryOverlayLabel.setStyleSheet("""
    #         QLabel {
    #             background-color: rgba(50, 50, 50, 220);
    #             color: white;
    #             padding: 10px;
    #             border-radius: 8px;
    #             font-size: 14pt;
    #         }
    #     """)
    #     self.temporaryOverlayLabel.setWindowFlags(qt.Qt.ToolTip)
    #     self.temporaryOverlayLabel.adjustSize()

    #     cursorPos = qt.QCursor.pos()
    #     self.temporaryOverlayLabel.move(cursorPos + qt.QPoint(20, 20))
    #     self.temporaryOverlayLabel.show()

    #     class ClickFilter(qt.QObject):
    #         def __init__(self, parent, label):
    #             super(ClickFilter, self).__init__(parent)
    #             self.label = label

    #         def eventFilter(self, obj, event):
    #             if event.type() == qt.QEvent.MouseButtonPress:
    #                 self.label.hide()
    #                 self.label.deleteLater()
    #                 slicer.util.mainWindow().removeEventFilter(self)
    #                 return True
    #             return False

    #     self.clickFilter = ClickFilter(slicer.util.mainWindow(), self.temporaryOverlayLabel)
    #     slicer.util.mainWindow().installEventFilter(self.clickFilter)


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
