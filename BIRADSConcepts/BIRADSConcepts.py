import inspect
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
        # self.segmentEditorWidget.setAdvancedVisibility(False)
        self.segmentEditorWidget.AddSegmentButton.hide()
        self.segmentEditorWidget.RemoveSegmentButton.hide()
        self.segmentEditorWidget.Show3DButton.hide()
        self.segmentEditorWidget.SwitchToSegmentationsButton.hide()


        self.logic = BIRADSConceptsLogic()
        self.controller = ReaderStudyController(self.ui, self.logic, self.segmentEditorWidget)
        self.controller.hideStudyWidgets()

        for btn in self.segmentEditorWidget.findChildren(qt.QComboBox):
            try:
                text = btn.currentText
                print(f"objectName: {text}")
            except:
                pass

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
        self.segmentEditorWidget = segmentEditorWidget

        self.ui.startStudyButton.connect('clicked(bool)', self.startStudy)
        self.ui.nextQuestionButton.connect('clicked(bool)', self.validateBiradsAndShowDensity)

        self.ui.biradsRight4.toggled.connect(lambda: self.ui.biradsRight4SubGroup.show() if self.ui.biradsRight4.isChecked() else self.ui.biradsRight4SubGroup.hide())
        self.ui.biradsLeft4.toggled.connect(lambda: self.ui.biradsLeft4SubGroup.show() if self.ui.biradsLeft4.isChecked() else self.ui.biradsLeft4SubGroup.hide())

        slicer.util.setDataProbeVisible(False)

        for side in ["right", "left"]:
            massYes = getattr(self.ui, f"mass{side.capitalize()}Yes")
            massNo = getattr(self.ui, f"mass{side.capitalize()}No")
            massYes.toggled.connect(lambda checked, s=side: self.toggleMassSubmenus(s))
            massNo.toggled.connect(lambda checked, s=side: self.toggleMassSubmenus(s))
            noneCheckBox = getattr(self.ui, f"{side}FeatureNone")
            featuresGroup = getattr(self.ui, f"{side}MassFeaturesGroup")

            noneCheckBox.toggled.connect(lambda checked, s=side: self.updateAssociatedFeatureSelections(s))
            for cb in featuresGroup.findChildren(qt.QCheckBox):
                if cb != noneCheckBox:
                    cb.toggled.connect(lambda checked, s=side: self.ensureNoneNotChecked(s))
        
            calcificationsYes = getattr(self.ui, f"{side}CalcificationsYes")
            calcificationsNo = getattr(self.ui, f"{side}CalcificationsNo")

            calcificationsYes.toggled.connect(lambda checked, s=side: self.toggleCalcificationSubmenus(s))
            calcificationsNo.toggled.connect(lambda checked, s=side: self.toggleCalcificationSubmenus(s, show=False))

            morphologySuss = getattr(self.ui, f"{side}MorphologySuspicious")
            morphologySuss.toggled.connect(lambda checked, s=side: self.toggleSuspiciousMorphologySubgroup(s))

            asymmetryYes = getattr(self.ui, f"{side}AsymmetryYes")
            asymmetryNo = getattr(self.ui, f"{side}AsymmetryNo")
            asymmetryYes.toggled.connect(lambda checked, s=side: self.toggleAsymmetrySubtypes(s))
            asymmetryNo.toggled.connect(lambda checked, s=side: self.toggleAsymmetrySubtypes(s, show=False))

            archDistortionNA = getattr(self.ui, f"{side}ArchitecturalDistortionNA")

            archDistortionNA.setEnabled(False)
            massYes.toggled.connect(lambda checked, s=side: self.updateArchDistortionAvailability(s))
            massNo.toggled.connect(lambda checked, s=side: self.updateArchDistortionAvailability(s))

            self.toggleCalcificationSubmenus(side=side, show=False)

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
        self.ui.rightAsymmetryGroup.hide()
        self.ui.rightAsymmetrySubtypeGroup.hide()
        self.ui.rightArchDistortionGroup.hide()
        self.ui.rightCalcificationsGroup.hide()
        self.ui.rightCalcificationsMorphologyGroup.hide()
        self.ui.rightSuspiciousMorphologySubGroup.hide()
        self.ui.rightCalcificationsDistributionGroup.hide()
        self.ui.leftAssessmentLabel.hide()
        self.ui.leftMassGroup.hide()
        self.ui.leftMassShapeGroup.hide()
        self.ui.leftMassMarginGroup.hide()
        self.ui.leftMassDensityGroup.hide()
        self.ui.leftMassFeaturesGroup.hide()
        self.ui.leftAsymmetryGroup.hide()
        self.ui.leftAsymmetrySubtypeGroup.hide()
        self.ui.leftArchDistortionGroup.hide()
        self.ui.leftCalcificationsGroup.hide()
        self.ui.leftCalcificationsMorphologyGroup.hide()
        self.ui.leftSuspiciousMorphologySubGroup.hide()
        self.ui.leftCalcificationsDistributionGroup.hide()
        self.segmentEditorWidget.hide()

    def showBiradsSection(self):
        self.ui.instructionLabel.setText("Please, read this case and provide the BI-RADS score per breast.")
        self.ui.instructionLabel.show()
        self.ui.status_checked.show()
        self.ui.biradsRightGroup.show()
        self.ui.biradsLeftGroup.show()
        self.ui.nextQuestionButton.show()

    def validateBiradsAndShowDensity(self):
        self.ui.nextQuestionButton.show()  
        self.ui.save_and_next.hide()

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
        
        self.setNextButtonCallback(self.validateDensity)
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

        self.showBreastAssessment(side="right")
    
    def showBreastAssessment(self, side):
        self.ui.instructionLabel.hide()
        self.ui.densityRightGroup.hide()
        self.ui.densityLeftGroup.hide()

        # Reset to 4-up layout
        slicer.app.layoutManager().setLayout(501)
        self.setupLayout(self.volume_map)

        # Hide all segmentations
        for tag in ["RCC", "RMLO", "LCC", "LMLO"]:
            segNode = slicer.mrmlScene.GetFirstNodeByName(f"{tag}-Segmentations")
            if segNode and segNode.GetDisplayNode():
                segNode.GetDisplayNode().SetVisibility(False)
        
        # Properly deactivate segmentation tools
        self.segmentEditorWidget.setSegmentationNode(None)
        self.segmentEditorWidget.setSourceVolumeNode(None)
        self.segmentEditorWidget.setMRMLSegmentEditorNode(None)
        self.segmentEditorWidget.setCurrentSegmentID("")  # Clear current segment
        self.segmentEditorWidget.hide()



        if side == "left":
            self.ui.rightAssessmentLabel.hide()
        getattr(self.ui, f"{side}AssessmentLabel").show()
        getattr(self.ui, f"{side}MassGroup").show()
        getattr(self.ui, f"{side}AsymmetryGroup").show()
        getattr(self.ui, f"{side}ArchDistortionGroup").show()
        getattr(self.ui, f"{side}CalcificationsGroup").show()

        self.ui.nextQuestionButton.setText("Next Question")
        self.setNextButtonCallback(lambda: self.validateMass(side=side))
    
    def validateMass(self, side):
        sideCapital = side.capitalize()
        sideLower = side.lower()

        # ---- MASS CHECK ---- #
        isMass = self.getSelectedButtonText(getattr(self.ui, f"{sideLower}MassGroup"))
        if not isMass:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select Yes or No for mass presence.")
            return
        
        if isMass.lower() == "yes":
            for name, msg in [
                (f"{sideLower}MassShapeGroup", "mass shape"),
                (f"{sideLower}MassMarginGroup", "mass margin"),
                (f"{sideLower}MassDensityGroup", "mass density")
            ]:
                if not self.getSelectedButtonText(getattr(self.ui, name)):
                    qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"Please select a {msg}.")
                    return
            
            features = [getattr(self.ui, f"{sideLower}Feature{name}") for name in ["SkinRetraction", "NippleRetraction", "SkinThickening", "TrabecularThickening",
            "AxillaryAdenopathy", "ArchitecturalDistortion", "Calcifications", "None"]]
            selected = [cb for cb in features if cb.isChecked()]
            if not selected:
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select at least one associated feature.")
                return
        
        # ---- ASYMMETRY CHECK ---- #
        asymmetry = self.getSelectedButtonText(getattr(self.ui, f"{sideLower}AsymmetryGroup"))
        if not asymmetry:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"Please answer the {sideCapital} asymmetry question.")
            return
        if asymmetry.lower() == "yes":
            if not any(getattr(self.ui, f"{sideLower}Asymmetry{name}").isChecked() for name in ["Focal", "Global", "Developing"]):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", "Please select at least one asymmetry type.")
                return
        
        # ---- ARCHITECTURAL DISTORTION CHECK ---- #
        if not any(getattr(self.ui, f"{sideLower}ArchitecturalDistortion{name}").isChecked() for name in ["Yes", "No", "NA"]):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"Please answer the {sideCapital} architectural distortion question.")
            return
        
        # ---- CALCIFICATIONS CHECK ---- #
        calcifications = self.getSelectedButtonText(getattr(self.ui, f"{sideLower}CalcificationsGroup"))
        if not calcifications:
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"Please answer the {sideCapital} calcifications question.")
            return
        if calcifications.lower() == "yes":
            for name, msg in [
                (f"{sideLower}CalcificationsMorphologyGroup", "calcification morphology"),
                (f"{sideLower}CalcificationsDistributionGroup", "calcification distribution") 
            ]:
                if not self.getSelectedButtonText(getattr(self.ui, name)):
                    qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"Please select a {msg}.")
                    return
        self.promptQuestionLockConfirmation(side=side)

    def promptQuestionLockConfirmation(self, side: str,):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Confirm Answers")
        msgBox.setText("Do you want to modify your answers?\nIf you press Continue, you will only be able to edit them at the end of the case.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
        msgBox.button(qt.QMessageBox.Ok).setText("Continue")
        msgBox.button(qt.QMessageBox.Cancel).setText("Edit answers")
        ret = msgBox.exec_()

        sideCapital = side.capitalize()

        if ret == qt.QMessageBox.Ok:
            getattr(self.ui, f"{side}MassGroup").hide()
            getattr(self.ui, f"{side}MassShapeGroup").hide()
            getattr(self.ui, f"{side}MassMarginGroup").hide()
            getattr(self.ui, f"{side}MassDensityGroup").hide()
            getattr(self.ui, f"{side}MassFeaturesGroup").hide()
            getattr(self.ui, f"{side}AsymmetryGroup").hide()
            getattr(self.ui, f"{side}AsymmetrySubtypeGroup").hide()
            getattr(self.ui, f"{side}ArchDistortionGroup").hide()
            getattr(self.ui, f"{side}CalcificationsGroup").hide()
            getattr(self.ui, f"{side}CalcificationsMorphologyGroup").hide()
            getattr(self.ui, f"{side}SuspiciousMorphologySubGroup").hide()
            getattr(self.ui, f"{side}CalcificationsDistributionGroup").hide()

            massYes = getattr(self.ui, f"mass{sideCapital}Yes")
            asimmetryYes = getattr(self.ui, f"{side}AsymmetryYes")
            calcificationsYes = getattr(self.ui, f"{side}CalcificationsYes")
            archDistortionYes = getattr(self.ui, f"{side}ArchitecturalDistortionYes")

            if massYes.isChecked() or asimmetryYes.isChecked() or calcificationsYes.isChecked() or archDistortionYes.isChecked():
                if side == "right":
                    self.runCCSegmentation(side="right")
                else:
                    self.runCCSegmentation(side="left")
            else:
                getattr(self.ui, f"{side}AssessmentLabel").hide()
                if side == "right":
                    self.showBreastAssessment(side="left")
                else:
                    self.reviewBreastAssessments()

 
    def startBreastSegmentationSequence(self, viewTag: str, side: str):
        self.segmentationQueue = []
        sideCapital = side.capitalize()
        massYes = getattr(self.ui, f"mass{sideCapital}Yes")
        asymmetryYes = getattr(self.ui, f"{side}AsymmetryYes")
        calcificationsYes = getattr(self.ui, f"{side}CalcificationsYes")
        archDistortionYes = getattr(self.ui, f"{side}ArchitecturalDistortionYes")

        if massYes.isChecked():
            self.segmentationQueue.append(lambda: self.segmentMass(viewTag, side))
            if asymmetryYes.isChecked():
                self.segmentationQueue.append(lambda: self.segmentAsymmetry(viewTag, side))
                if calcificationsYes.isChecked():
                    self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag, side))
            else:
                if calcificationsYes.isChecked():
                   self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag, side))
        else:
            if asymmetryYes.isChecked():
                self.segmentationQueue.append(lambda: self.segmentAsymmetry(viewTag, side))
                if archDistortionYes.isChecked():
                    self.segmentationQueue.append(lambda: self.segmentDistortion(viewTag, side))
                if calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag, side)) 
                else:
                   if calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag, side))
            else:
                if archDistortionYes.isChecked():
                    self.segmentationQueue.append(lambda: self.segmentDistortion(viewTag, side))
                if calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag, side)) 
                else:
                   if calcificationsYes.isChecked():
                       self.segmentationQueue.append(lambda: self.segmentCalcifications(viewTag, side)) 
        self.runNextSegmentationTask(viewTag, side)
    
    def runCCSegmentation(self, side: str):
        if side == "right":
            self.startBreastSegmentationSequence("RCC", side)
        else:
            self.startBreastSegmentationSequence("LCC", side)
    
    def runMLOSegmentation(self, side: str):
        if side == "right":
            SegNode = slicer.mrmlScene.GetFirstNodeByName("RCC-Segmentations")
            if SegNode:
                displayNode = SegNode.GetDisplayNode()
                if displayNode:
                    displayNode.SetVisibility(False)

            self.startBreastSegmentationSequence("RMLO", side)
        else:
            SegNode = slicer.mrmlScene.GetFirstNodeByName("LCC-Segmentations")
            if SegNode:
                displayNode = SegNode.GetDisplayNode()
                if displayNode:
                    displayNode.SetVisibility(False)

            self.startBreastSegmentationSequence("LMLO", side)

    def runNextSegmentationTask(self, viewTag: str, side: str):
        if not self.segmentationQueue:
            if viewTag=="RCC" and side == "right":
                print("Im in this if: if viewTag=='RCC' and side == 'right'")
                self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
                self.setNextButtonCallback(lambda: self.promptSegmentation("RMLO", "right"))
            elif viewTag == "RMLO" and side == "right":
                self.ui.nextQuestionButton.setText("Continue to left breast assessment")
                self.setNextButtonCallback(lambda: self.showBreastAssessment("left"))
            elif viewTag == "LCC" and side == "left":
                self.ui.nextQuestionButton.setText("Continue to L-MLO segmentation")
                self.setNextButtonCallback(lambda: self.promptSegmentation("LMLO", "left"))
            elif viewTag=="LMLO" and side == "left":
                self.ui.nextQuestionButton.setText("Continue to case review")
                self.reviewBreastAssessments()

        nextTask = self.segmentationQueue.pop(0)
        nextTask()

    def segmentMass(self, viewTag: str, side: str):
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the mass in the {viewTag} view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.ui.nextQuestionButton.setText("Add next segment")
        self.launchSegmentEditor(viewTag, f"{viewTag}-{side}-Mass")
        # msgBox = qt.QMessageBox(slicer.util.mainWindow())
        # msgBox.setWindowTitle("Segmentation Instruction")
        # msgBox.setText(f"Please segment the mass in the {viewTag} view.")
        # msgBox.setStandardButtons(qt.QMessageBox.Ok)
        # msgBox.exec_()
        self.showTemporaryInstruction(f"Please segment the mass in the {viewTag} view.")
        self.setNextButtonCallback(lambda: self.validateMassSegmentation(viewTag, side))

        # try:
        #     self.ui.nextQuestionButton.clicked.disconnect()
        # except TypeError:
        #     pass

        # self.ui.nextQuestionButton.clicked.connect(lambda: self.validateMassSegmentation(viewTag, side))

    def validateMassSegmentation(self, viewTag: str, side: str):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        massID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(f"{viewTag}-{side}-Mass")
        if self.isSegmentEmpty(segmentationNode, massID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Mass segment is empty. Please complete it.")
            return

        self.segmentationQueue.insert(0, lambda: self.segmentMargins(viewTag, side))
        self.runNextSegmentationTask(viewTag, side)
    
    def segmentMargins(self, viewTag: str, side: str):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment the margins of the mass in the {viewTag} view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()

        segmentationNode = self.segmentEditorWidget.segmentationNode()
        segmentName = f"{viewTag}-{side}-Margins"
        existingID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(segmentName)
        if existingID:
            marginsSegmentID = existingID
        else:
            marginsSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(segmentName)
        self.segmentEditorWidget.setCurrentSegmentID(marginsSegmentID)

        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the margins of the mass in the {viewTag} view.\n"
                                        "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        self.associatedFeaturesToSegment = self.getSelectedFeatures(viewTag, side)
        noMoreTasks = not self.segmentationQueue and len(self.associatedFeaturesToSegment)==0
        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass

        self.ui.nextQuestionButton.clicked.connect(lambda: self.validateMarginsSegmentation(viewTag, side, noMoreTasks))
        if noMoreTasks:
            if viewTag == "RCC" and side == "right":
                print(f"Im in if viewTag == 'RCC' and side == 'right':")
                self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
            elif viewTag == "RMLO" and side == "right":
               self.ui.nextQuestionButton.setText("Continue to left breast assessment") 
            elif viewTag == "LCC" and side == "left":
               self.ui.nextQuestionButton.setText("Continue to L-MLO segmentation")
            elif viewTag == "LMLO" and side == "left":
               self.ui.nextQuestionButton.setText("Continue to case review")
        else:
            self.ui.nextQuestionButton.setText("Add next segment")
            
    
    def validateMarginsSegmentation(self, viewTag: str, side: str, noMoreTasksAfterMargins: bool):
        print(f"I'm in validateMarginsSegmentation with {viewTag} and {side}")
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        marginsID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(f"{viewTag}-{side}-Margins")
        if self.isSegmentEmpty(segmentationNode, marginsID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", "Margins segment is empty. Please complete it.")
            return
        
        massFeaturesGroup = getattr(self.ui, f"{side}MassFeaturesGroup")
        if not noMoreTasksAfterMargins:
            print(f"I'm in if not noMoreTasksAfterMargins")
            if "CC" in viewTag:
                print("I'm in if 'CC' in viewTage")
                print(f"side")
                if any(cb.isChecked() for cb in massFeaturesGroup.findChildren(qt.QCheckBox) if cb.text not in ["None of the above", "Axillary adenopathy"]):
                    print("I'm in the if any if in the if CC in validateMargins")
                    self.currentFeatureIndex = 0
                    self.segmentNextFeatureInQueue(viewTag, side)
                else:
                    print("I'm in the else of the if any if in the if CC in validateMargins")
                    self.runNextSegmentationTask(viewTag, side)
            elif "MLO" in viewTag:
                if any(cb.isChecked() for cb in massFeaturesGroup.findChildren(qt.QCheckBox) if cb.text != "None of the above"):
                    self.currentFeatureIndex = 0
                    self.segmentNextFeatureInQueue(viewTag, side)
                else:
                    self.runNextSegmentationTask(viewTag, side)
        else:
            if viewTag == "RCC":
                self.promptSegmentation("RMLO", "right")
            elif viewTag == "RMLO":
                msgBox = qt.QMessageBox(slicer.util.mainWindow())
                msgBox.setWindowTitle("Confirm Answers")
                msgBox.setText("Do you want to modify your segmentations?\nIf you press Continue, you will only be able to edit them at the end of the case.")
                msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msgBox.button(qt.QMessageBox.Ok).setText("Continue")
                msgBox.button(qt.QMessageBox.Cancel).setText("Edit answers")
                ret = msgBox.exec_()

                if ret == qt.QMessageBox.Ok:
                    self.showBreastAssessment("left")
            elif viewTag == "LCC":
                self.promptSegmentation("LMLO", "left")
            elif viewTag == "LMLO":
                self.reviewBreastAssessments()
                
    def segmentNextFeatureInQueue(self, viewTag: str, side: str):
        if self.currentFeatureIndex >= len(self.associatedFeaturesToSegment):
            self.runNextSegmentationTask(viewTag, side)
            return

        feature = self.associatedFeaturesToSegment[self.currentFeatureIndex]
        self.currentFeatureIndex += 1

        segmentationNode = self.segmentEditorWidget.segmentationNode()
        segmentID = segmentationNode.GetSegmentation().AddEmptySegment(f"{viewTag}-{side}-{feature}")
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
        self.setNextButtonCallback(lambda: self.validateFeatureSegmentation(segmentID, feature, viewTag, side, noMoreTasks))
        
        if noMoreTasks:
            if viewTag == "RCC" and side == "right":
                self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
            elif viewTag == "RMLO" and side == "right":
               self.ui.nextQuestionButton.setText("Continue to left breast assessment") 
            elif viewTag == "LCC" and side == "left":
               self.ui.nextQuestionButton.setText("Continue to L-MLO segmentation")
            elif viewTag == "LMLO" and side == "left":
               self.ui.nextQuestionButton.setText("Continue to case review")
        else:
            self.ui.nextQuestionButton.setText("Add next segment")

    def validateFeatureSegmentation(self, segmentID: str, feature: str, viewTag: str, side: str, noMoreTasksAfterFeatures: bool):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", f"{feature} segment is empty. Please complete it.")
            return
        if not noMoreTasksAfterFeatures:
            self.segmentNextFeatureInQueue(viewTag, side)
        else:
            if viewTag == "RCC":
                self.promptSegmentation("RMLO", "right")
            elif viewTag == "RMLO":
                msgBox = qt.QMessageBox(slicer.util.mainWindow())
                msgBox.setWindowTitle("Confirm Answers")
                msgBox.setText("Do you want to modify your segmentations?\nIf you press Continue, you will only be able to edit them at the end of the case.")
                msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msgBox.button(qt.QMessageBox.Ok).setText("Continue")
                msgBox.button(qt.QMessageBox.Cancel).setText("Edit answers")
                ret = msgBox.exec_()

                if ret == qt.QMessageBox.Ok:
                    self.showBreastAssessment("left")
            elif viewTag == "LCC":
                self.promptSegmentation("LMLO", "left")
            elif viewTag == "LMLO":
                self.reviewBreastAssessments()
                    
    def segmentAsymmetry(self, viewTag: str, side: str):
        self.startGenericSegmentation(f"{viewTag}-{side}-Asymmetry", viewTag, side)

    def segmentDistortion(self, viewTag:str, side: str):
        self.startGenericSegmentation(f"{viewTag}-{side}-MainDistortion", viewTag, side)

    def segmentCalcifications(self, viewTag: str, side:str):
        self.startGenericSegmentation(f"{viewTag}-{side}-MainCalcifications", viewTag, side)

    def startGenericSegmentation(self, name: str, viewTag: str, side: str):
        self.ui.instructionLabel.show()
        self.ui.instructionLabel.setText(f"Please segment the {name} in the {viewTag} view.\n" \
                "Tip: use the threshold tool and then the paint and erase tools. You can also use the smoothing function.")
        # if len(self.segmentationQueue) == 0 and viewTag=="RCC":
        #     self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
        # elif len(self.segmentationQueue) == 0 and viewTag=="RMLO":
        #     self.ui.nextQuestionButton.setText("Continue to left breast assessment") 
        # else:
        #     self.ui.nextQuestionButton.setText("Add next segment")

        self.launchSegmentEditor(viewTag, name)

        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        msgBox.setWindowTitle("Segmentation Instruction")
        msgBox.setText(f"Please segment {name} in the {viewTag} view.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok)
        msgBox.exec_()

        if not self.segmentationQueue:
            if viewTag == "RCC" and side == "right":
                print(f"Im in if viewTag == 'RCC' and side == 'right':")
                self.ui.nextQuestionButton.setText("Continue to R-MLO segmentation")
            elif viewTag == "RMLO" and side == "right":
               self.ui.nextQuestionButton.setText("Continue to left breast assessment") 
            elif viewTag == "LCC" and side == "left":
               self.ui.nextQuestionButton.setText("Continue to L-MLO segmentation")
            elif viewTag == "LMLO" and side == "left":
               self.ui.nextQuestionButton.setText("Continue to case review")
        else:
            self.ui.nextQuestionButton.setText("Add next segment") 

        self.setNextButtonCallback(lambda: self.validateGenericSegmentation(name, viewTag, side))

    def validateGenericSegmentation(self, segmentID: str, viewTag: str, side: str):
        segmentationNode = self.segmentEditorWidget.segmentationNode()
        if self.isSegmentEmpty(segmentationNode, segmentID, self.referenceVolumeNode):
            qt.QMessageBox.warning(slicer.util.mainWindow(), "Empty Segment", f"{segmentID} is empty. Please complete it.")
            return

        if not self.segmentationQueue:
            if viewTag == "RCC":
                self.promptSegmentation("RMLO", "right")
            elif viewTag == "RMLO":
                msgBox = qt.QMessageBox(slicer.util.mainWindow())
                msgBox.setWindowTitle("Confirm Answers")
                msgBox.setText("Do you want to modify your segmentations?\nIf you press Continue, you will only be able to edit them at the end of the case.")
                msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msgBox.button(qt.QMessageBox.Ok).setText("Continue")
                msgBox.button(qt.QMessageBox.Cancel).setText("Edit answers")
                ret = msgBox.exec_()

                if ret == qt.QMessageBox.Ok:
                    self.showBreastAssessment("left")
            elif viewTag == "LCC":
                self.promptSegmentation("LMLO", "left")
            elif viewTag == "LMLO":
                self.reviewBreastAssessments()
        else:
            self.runNextSegmentationTask(viewTag, side)
    
    def promptSegmentation(self, viewTag: str, side: str):
        msgBox = qt.QMessageBox(slicer.util.mainWindow())
        laterality = "R" if side == "right" else "L"
        msgBox.setWindowTitle(f"Continue to {laterality}-MLO?")
        msgBox.setText("Do you want to modify the segmentations?\nIf you press Continue, you will only be able to edit them at the end of the case.")
        msgBox.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
        msgBox.button(qt.QMessageBox.Ok).setText("Continue")
        msgBox.button(qt.QMessageBox.Cancel).setText("Edit segmentations")
        ret = msgBox.exec_()

        if ret == qt.QMessageBox.Ok:
            if viewTag == "RCC":
                self.runCCSegmentation(side)
            elif "MLO" in viewTag:
                self.runMLOSegmentation(side)
    
    def toggleMassSubmenus(self, side: str):
        sideCapital = side.capitalize()
        massYes = getattr(self.ui, f"mass{sideCapital}Yes")
        massShapeGroup = getattr(self.ui, f"{side}MassShapeGroup")
        massMarginGroup = getattr(self.ui, f"{side}MassMarginGroup")
        massDensityGroup = getattr(self.ui, f"{side}MassDensityGroup")
        massFeaturesGroup = getattr(self.ui, f"{side}MassFeaturesGroup")

        for grp in [massShapeGroup, massMarginGroup, massDensityGroup, massFeaturesGroup]:
            grp.setVisible(massYes.isChecked())
            
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
        
        comboBoxes = self.segmentEditorWidget.findChildren(qt.QComboBox)
        if len(comboBoxes) >= 2:
            comboBoxes[0].setEnabled(False)
            comboBoxes[1].setEnabled(False)
            print(comboBoxes[0].currentText)
    
    def updateAssociatedFeatureSelections(self, side: str):
        noneCheckBox = getattr(self.ui, f"{side}FeatureNone")
        featuresGroup = getattr(self.ui, f"{side}MassFeaturesGroup")

        if noneCheckBox.isChecked():
            for cb in featuresGroup.findChildren(qt.QCheckBox):
                if cb != noneCheckBox and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
    
    def ensureNoneNotChecked(self, side: str):
        noneCheckBox = getattr(self.ui, f"{side}FeatureNone")
        featuresGroup = getattr(self.ui, f"{side}MassFeaturesGroup")

        if any(cb.isChecked() for cb in featuresGroup.findChildren(qt.QCheckBox) if cb != noneCheckBox):
            noneCheckBox.blockSignals(True)
            noneCheckBox.setChecked(False)
            noneCheckBox.blockSignals(False)        
    
    def updateArchDistortionAvailability(self, side: str):
        sideCapital = side.capitalize()
        massYes = getattr(self.ui, f"mass{sideCapital}Yes")
        archDistortionYes = getattr(self.ui, f"{side}ArchitecturalDistortionYes")
        archDistortionNo = getattr(self.ui, f"{side}ArchitecturalDistortionNo")
        archDistortionNA = getattr(self.ui, f"{side}ArchitecturalDistortionNA") 
        if massYes.isChecked():
            archDistortionYes.setChecked(False)
            archDistortionNo.setChecked(False)
            archDistortionNA.setEnabled(True)
            archDistortionYes.setEnabled(False)
            archDistortionNo.setEnabled(False)
            archDistortionNA.setChecked(True)
        else:
            for btn in [archDistortionYes, archDistortionNo, archDistortionNA]:
                btn.setAutoExclusive(False)
                btn.setChecked(False)
                btn.setAutoExclusive(True)

            archDistortionNA.setEnabled(False)
            archDistortionYes.setEnabled(True)
            archDistortionNo.setEnabled(True)            

    def toggleCalcificationSubmenus(self, side: str, show: bool=True):
        getattr(self.ui, f"{side}CalcificationsMorphologyGroup").setVisible(show)
        getattr(self.ui, f"{side}CalcificationsDistributionGroup").setVisible(show)
        if not show:
            getattr(self.ui, f"{side}MorphologySuspicious").setChecked(False)
            self.toggleSuspiciousMorphologySubgroup(side=side, show=False)
    
    def toggleSuspiciousMorphologySubgroup(self, side: str, show: bool=True):
        getattr(self.ui, f"{side}SuspiciousMorphologySubGroup").setVisible(show)
    
    def toggleAsymmetrySubtypes(self, side: str, show: bool=True):
        getattr(self.ui, f"{side}AsymmetrySubtypeGroup").setVisible(show)

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
            return True
    
    def getSelectedFeatures(self, viewTag: str, side: str):
        features = []
        massFeaturesGroup = getattr(self.ui, f"{side}MassFeaturesGroup")
        if "CC" in viewTag:
            for checkbox in massFeaturesGroup.findChildren(qt.QCheckBox):
                if checkbox.isChecked() and checkbox.text != "None of the above" and checkbox.text != "Axillary adenopathy":
                    features.append(checkbox.text)
        elif "MLO" in viewTag:
            for checkbox in massFeaturesGroup.findChildren(qt.QCheckBox):
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
    
    def reviewBreastAssessments(self):
        self.ui.instructionLabel.hide()
        # Reset to 4-up layout
        slicer.app.layoutManager().setLayout(501)
        self.setupLayout(self.volume_map)
        # Hide all segmentations
        for tag in ["RCC", "RMLO", "LCC", "LMLO"]:
            segNode = slicer.mrmlScene.GetFirstNodeByName(f"{tag}-Segmentations")
            if segNode and segNode.GetDisplayNode():
                segNode.GetDisplayNode().SetVisibility(False)
        
        self.segmentEditorWidget.setSegmentationNode(None)
        self.segmentEditorWidget.setSourceVolumeNode(None)
        self.segmentEditorWidget.setMRMLSegmentEditorNode(None)
        self.segmentEditorWidget.setCurrentSegmentID("")  # Clear current segment
        self.segmentEditorWidget.hide()
        
        for side in ["right", "left"]:
            isMass = self.getSelectedButtonText(getattr(self.ui, f"{side}MassGroup"))
            isAsymmetry = self.getSelectedButtonText(getattr(self.ui, f"{side}AsymmetryGroup"))
            isCalcifications = self.getSelectedButtonText(getattr(self.ui, f"{side}CalcificationsGroup"))
            getattr(self.ui, f"{side}AssessmentLabel").setText(f"Review of {side} breast assessment") 
            getattr(self.ui, f"{side}AssessmentLabel").show()
            getattr(self.ui, f"{side}MassGroup").show()
            print(f"{isMass=}")
            if isMass == "Yes":
                getattr(self.ui, f"{side}MassShapeGroup").show()
                getattr(self.ui, f"{side}MassMarginGroup").show()
                getattr(self.ui, f"{side}MassDensityGroup").show()
                getattr(self.ui, f"{side}MassFeaturesGroup").show()
            getattr(self.ui, f"{side}AsymmetryGroup").show()
            print(f"{isAsymmetry=}")
            if isAsymmetry == "Yes":
                getattr(self.ui, f"{side}AsymmetrySubtypeGroup").show()
            getattr(self.ui, f"{side}ArchDistortionGroup").show()
            if not any(getattr(self.ui, f"{side}ArchitecturalDistortion{name}").isChecked() for name in ["Yes", "No", "NA"]):
                qt.QMessageBox.warning(slicer.util.mainWindow(), "Incomplete", f"Please answer the {side.capitalize()} architectural distortion question.")
                return
            getattr(self.ui, f"{side}CalcificationsGroup").show()
            print(f"{isCalcifications=}")
            if isCalcifications == "Yes":
                getattr(self.ui, f"{side}CalcificationsMorphologyGroup").show()
                getattr(self.ui, f"{side}CalcificationsDistributionGroup").show()
                if getattr(self.ui, f"{side}MorphologySuspicious").isChecked():
                    getattr(self.ui, f"{side}SuspiciousMorphologySubGroup").show()

        
        self.ui.nextQuestionButton.setText("Save and review segmentations")
        # self.setNextButtonCallback(self.reviewSegmentations)

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
    
    def setNextButtonCallback(self, callback):
        try:
            self.ui.nextQuestionButton.clicked.disconnect()
        except TypeError:
            pass
        self.ui.nextQuestionButton.clicked.connect(callback)

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
                background-color: #f0f0f0;
                border: 2px solid gray;
                border-radius: 10px;
            }
            QLabel {
                font-weight: bold;
                color: black;
                padding: 10px;
                font-size: 15pt;
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
