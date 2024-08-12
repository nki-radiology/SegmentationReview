import logging
import os


import vtk
from pathlib import Path
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import ctk
import qt


try:
    import pandas as pd
    import numpy as np
    import SimpleITK as sitk
except:
    slicer.util.pip_install('pandas')
    slicer.util.pip_install('numpy')
    slicer.util.pip_install('SimpleITK')
    
    import pandas as pd
    import numpy as np
    import SimpleITK as sitk
#
# ProstaSeg
#

class ProstaSeg(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "ProstaSeg"
        self.parent.categories = ["Examples"]  
        self.parent.dependencies = []  
        self.parent.contributors = ["Anna Zapaishchykova (BWH), Dr. Benjamin H. Kann, AIM-Harvard"]  
        self.parent.helpText = """
Slicer3D extension for rating using Likert-type score Deep-learning generated segmentations, with segment editor funtionality. 
Created to speed up the validation process done by a clinician - the dataset loads in one batch with no need to load masks and volumes separately.
It is important that each nii file has a corresponding mask file with the same name and the suffix _mask.nii
"""
       
        self.parent.acknowledgementText = """
This file was developed by Anna Zapaishchykova, BWH. 
"""


#
# ProstaSegWidget
#

class ProstaSegWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False
        self.volume_node = None
        self.segmentation_node = None
        self.segmentation_visible = False
        self.segmentation_color = [1, 0, 0]
        self.image_files = []
        self.segmentation_files = []
        self.directory=None
        self.current_index=0
        self.likert_scores = []
        self.n_files = 0
        self.current_df = None

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        # Setup the module widget
        ScriptedLoadableModuleWidget.setup(self)

        # Add directory input widget
        self._createDirectoryWidget()

        # Add custom UI widget
        self._createCustomUIWidget()

        # Add segment editor widget
        self._createSegmentEditorWidget()

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        
        # self.ui.PathLineEdit = ctk.ctkDirectoryButton()
        
        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.atlasDirectoryButton.directoryChanged.connect(self.onAtlasDirectoryChanged)
        self.ui.save_next.connect('clicked(bool)', self.onSaveNextClicked)
        self.ui.previous.connect('clicked(bool)', self.onPreviousClicked)

    def _createDirectoryWidget(self):
        # Add collapsible input section
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Input path"
        self.layout.addWidget(parametersCollapsibleButton)

        # Add directory button to the input
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        self.atlasDirectoryButton = ctk.ctkDirectoryButton()
        parametersFormLayout.addRow("Directory: ", self.atlasDirectoryButton)

    def _createCustomUIWidget(self):
        # Load widget from .ui file (created by Qt Designer).
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/ProstaSeg.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

    def _createSegmentEditorWidget(self):
        """Create and initialize a customize Slicer Editor which contains just some the tools that we need for the segmentation"""

        import qSlicerSegmentationsModuleWidgetsPythonQt

        # advancedCollapsibleButton
        self.segmentEditorWidget = qSlicerSegmentationsModuleWidgetsPythonQt.qMRMLSegmentEditorWidget(
        )
        self.segmentEditorWidget.setMaximumNumberOfUndoStates(10)
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorWidget.unorderedEffectsVisible = False
        self.segmentEditorWidget.setEffectNameOrder([
            'Paint', 'Draw', 'Erase', 'Threshold', 'Smoothing',
        ])
        self.layout.addWidget(self.segmentEditorWidget)
        undoShortcut = qt.QShortcut(qt.QKeySequence('z'), self.segmentEditorWidget)
        undoShortcut.activated.connect(self.segmentEditorWidget.undo)

    def onAtlasDirectoryChanged(self, directory):
        try:
            if self.volume_node and slicer.mrmlScene.IsNodePresent(self.volume_node):
                slicer.mrmlScene.RemoveNode(self.volume_node)
            if self.segmentation_node and slicer.mrmlScene.IsNodePresent(self.segmentation_node):
                slicer.mrmlScene.RemoveNode(self.segmentation_node)
        except Exception as e:
            print(f"Error while removing nodes: {e}")

        # Clear the previously loaded image and segmentation
        if self.volume_node:
            slicer.mrmlScene.RemoveNode(self.volume_node)
        if self.segmentation_node:
            slicer.mrmlScene.RemoveNode(self.segmentation_node)

        # Set the new directory
        self.directory = directory

        # Initialize these variables at the beginning
        self.n_files = 0
        self.current_index = 0
        self.image_files = []
        self.segmentation_files = []

        # Load the existing annotations if the file exists
        annotated_files = set()
        if os.path.exists(directory + "/ProstaSeg_annotations.csv"):
            self.current_df = pd.read_csv(directory + "/ProstaSeg_annotations.csv")
            annotated_files = set(self.current_df['patientID'].values)

        else:
            columns = ['patientID', 'comment']
            self.current_df = pd.DataFrame(columns=columns)

        # Collect images and masks, skipping already annotated ones
        for folder in Path(directory).iterdir():
            if folder.is_dir():
                patientID = folder.name

                # Skip the file if it's already annotated
                if patientID in annotated_files:
                    continue

                # Initialize
                image_file = None
                seg_file = None

                # Iterate over files in the folder
                for file in folder.iterdir():
                    if file.is_file():
                        print(file)
                        # Check if the file contains 'image' in its name
                        if 'image' in file.name:
                            image_file = file

                        # Optionally check if the file contains 'segmentation' in its name
                        elif 'segmentation' in file.name.lower():
                            seg_file = file

                # Update loop iterables
                self.n_files += 1
                self.image_files.append(image_file)
                self.segmentation_files.append(seg_file)

        # Reset the UI to original
        self.resetUIElements()

        if self.n_files != 0:
            # Load the first case
            self.load_files()
        else:
            # Say that everything is already checked
            self.ui.var_check.setText("All files are checked!")
            self.ui.var_ID.setText('')
            print("All files checked")

    def resetUIElements(self):
        self.ui.var_comment.clear()
        print("All UI elements reset.")

    def onSaveNextClicked(self):
        # Get the file path where you want to save the segmentation node
        seg_file_path = self.image_files[self.current_index].parent / 'segmentation.seg.nrrd'

        # Save the segmentation node to file
        slicer.util.saveNode(self.segmentation_node, str(seg_file_path))

        # Add to csv of annotations
        new_result = {
            'patientID': seg_file_path.parent.name,
            'comment': self.ui.var_comment.toPlainText()
        }
        self.append_to_csv(new_result)

        # Go to next case
        self.goNext()

    def onPreviousClicked(self):
        # Return to previous case
        self.goPrevious()

    def goNext(self):
        try:
            if self.volume_node and slicer.mrmlScene.IsNodePresent(self.volume_node):
                slicer.mrmlScene.RemoveNode(self.volume_node)
            if self.segmentation_node and slicer.mrmlScene.IsNodePresent(self.segmentation_node):
                slicer.mrmlScene.RemoveNode(self.segmentation_node)
        except Exception as e:
            print(f"Error while removing nodes: {e}")

        if self.current_index < self.n_files - 1:
            self.current_index += 1
            self.load_files()
            self.resetUIElements()
        else:
            self.ui.var_check.setText("All files are checked!")
            self.ui.var_ID.setText('')
            print("All files checked")

    def goPrevious(self):
        if self.current_index > 0:
            try:
                if self.volume_node and slicer.mrmlScene.IsNodePresent(self.volume_node):
                    slicer.mrmlScene.RemoveNode(self.volume_node)
                if self.segmentation_node and slicer.mrmlScene.IsNodePresent(self.segmentation_node):
                    slicer.mrmlScene.RemoveNode(self.segmentation_node)
            except Exception as e:
                print(f"Error while removing nodes: {e}")

            self.current_index -= 1
            self.load_files()
            self.resetUIElements()

        else:
            print('Already at start of sequence!')

    def append_to_csv(self, new_row_data):
        # Define the required column order
        required_columns = [
            'patientID', 'comment'
        ]

        # Ensure all required columns are present in the new row, filling in None for any that are missing
        new_row = {column: new_row_data.get(column, None) for column in required_columns}

        # Create DataFrame for the new row
        df = pd.DataFrame([new_row])

        # Full path to the CSV file
        file_path = os.path.join(self.directory, 'ProstaSeg_annotations.csv')

        # Check if the file exists to determine whether to write headers
        file_exists = os.path.exists(file_path)

        # Append to the CSV without header if file exists, else with header
        df.to_csv(file_path, mode='a', index=False, header=not file_exists)
    
    def load_files(self):
        # Load image
        file_path = self.image_files[self.current_index]
        self.volume_node = slicer.util.loadVolume(file_path)
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

        # Retrieve segmentation path
        segmentation_file_path = self.segmentation_files[self.current_index]
        print(segmentation_file_path)

        # Initialize variables
        segment_id_fascia = None
        segment_id_prostate = None

        if segmentation_file_path is not None:
            # Load segmentation
            self.segmentation_node = slicer.util.loadSegmentation(segmentation_file_path)

            # Setting the visualization of the segmentation to outline only
            segmentationDisplayNode = self.segmentation_node.GetDisplayNode()
            segmentationDisplayNode.SetVisibility2DFill(False)  # Do not show filled region in 2D
            segmentationDisplayNode.SetVisibility2DOutline(True)  # Show outline in 2D
            segmentationDisplayNode.SetVisibility(True)

            seg = self.segmentation_node.GetSegmentation()
            for seg_id in seg.GetSegmentIDs():
                segment = seg.GetSegment(seg_id)
                if segment.GetName().lower() == 'fascia':
                    segment_id_fascia = seg_id
                elif segment.GetName().lower() == 'prostate':
                    segment_id_prostate = seg_id
                else:
                    segmentationDisplayNode.SetSegmentVisibility(seg_id, False)
                    
            # Check if 'Fascia' and 'Prostate' segments are already present, if not, create one
            # Fascia
            if segment_id_fascia is not None:
                print(f"The segment with label 'Fascia' already exists.")
            else:
                # Create a new segment with the specified label
                segment_id_fascia = seg.AddEmptySegment('Fascia')
                segment = seg.GetSegment(segment_id_fascia)
                if segment:
                    segment.SetName('Fascia')

        else:
            # Create a new segmentation node
            self.segmentation_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
            self.segmentation_node.SetName("Segmentation")

            # Add a display node to the segmentation node
            segmentation_display_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationDisplayNode')
            self.segmentation_node.SetAndObserveDisplayNodeID(segmentation_display_node.GetID())

            # Get the segmentation object from the node
            segmentation = self.segmentation_node.GetSegmentation()

            # Add segments with the specified labels
            for label in ["Prostate", "Fascia"]:
                segment_id = segmentation.AddEmptySegment(label)
                if label == "Prostate":
                    segment_id_prostate = segment_id

                segment = segmentation.GetSegment(segment_id)
                if segment:
                    segment.SetName(label)

        # Connect segmentation editor to the masks
        self.set_segmentation_and_mask_for_segmentation_editor()
        self.ui.var_check.setText(str(self.current_index) + " / " + str(self.n_files))
        self.ui.var_ID.setText(str(file_path.parent.name))

        # Check if prostate is already there
        if segment_id_prostate is None:
            slicer.util.infoDisplay("Please create or rename appropriate segment to 'Prostate'.")

    def set_segmentation_and_mask_for_segmentation_editor(self):
        slicer.app.processEvents()
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        self.segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        self.segmentEditorWidget.setSegmentationNode(self.segmentation_node)
        self.segmentEditorWidget.setSourceVolumeNode(self.volume_node)




























    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.GetNodeReference("InputVolume"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        #if inputParameterNode:
        #    self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True


        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.EndModify(wasModified)