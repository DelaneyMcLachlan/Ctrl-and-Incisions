import vtk
import cv2
import time
import zlib
import os
import Stats
import csv
import time
import sys

import numpy as np
from pathlib import Path
import calibration_io as cio
import hand_eye_cal_logic as he

from PySide6 import QtWidgets, QtCore, QtGui
from vtkMainWindow_ui import Ui_MainWindow
import vtkMainWindow_ui
print("USING UI FILE:", vtkMainWindow_ui.__file__)

# BASE_DIR = Path(__file__).resolve().parents[2]
# sys.path.insert(0, str(BASE_DIR))

# from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
# from sksurgerynditracker.nditracker import NDITracker
# from database.db import init_db, get_or_create_device, start_capture_session, end_capture_session, add_ultrasound_stream, add_tracking_stream, log_event, create_device_config

SRC_DIR = Path(__file__).resolve().parents[2]
PHASE5_DIR = SRC_DIR / "phase5_prototype"

sys.path.insert(0, str(PHASE5_DIR))
sys.path.insert(0, str(SRC_DIR))

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from sksurgerynditracker.nditracker import NDITracker
from phase5_prototype.data.db import (
    init_db,
    get_or_create_device,
    start_capture_session,
    end_capture_session,
    add_ultrasound_stream,
    add_tracking_stream,
    log_event,
    create_device_config,
)

from OverlayApp import OverlayApp

SPHERE_RADIUS = 15
NUM_TRACKING_FRAMES = 40
NUM_PORTS = 2
PORT_STYLUS = 0
PORT_CAMERA = 1
ERROR_THRESHOLD = 0.8

USE_FAKE_TRACKER = True

if USE_FAKE_TRACKER:
    from fake_tracker import FakeTracker


class QVTKViewer(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, video_source = 0, parent=None):
        super().__init__()
        self.setupUi(self)
        
        he_layout = QtWidgets.QGridLayout(self.frame_3)
        he_layout.setContentsMargins(8, 8, 8, 8)
        he_layout.setHorizontalSpacing(10)
        he_layout.setVerticalSpacing(6)

        he_layout.addWidget(self.beginHEButton, 0, 0)
        he_layout.addWidget(self.saveHEButton, 0, 1)
        he_layout.addWidget(self.loadHEButton, 1, 0)
        he_layout.addWidget(self.testHEToggle, 1, 1)

        # PLUS per frame buffers
        self.plusFramesGray = []
        self.plusTimes = []
        self.plusProbe16 = []
        self.plusStylus16 = []
        self.plusRef16 = []

        self.plusActive = False
        self.plusOutPath = None
        self.plusT0 = 0.0

        self._plusLastTime = 0.0

        self._plusLastProbe16 = None
        self._plusLastStylus16 = None
        self._plusLastRef16 = None

        self.plusProbeValid = []
        self.plusStylusValid = []
        self.plusRefValid = []

        self._plusLastProbeValid = False
        self._plusLastStylusValid = False
        self._plusLastRefValid = False

        # ---------- Fix icons/logos to use local assets ----------
        base_dir = Path(__file__).resolve().parent
        assets_dir = base_dir / "assets"

        def make_icon(filename: str) -> QtGui.QIcon:
            path = assets_dir / filename
            if path.exists():
                return QtGui.QIcon(str(path))
            return QtGui.QIcon()

        def make_pixmap(filename: str) -> QtGui.QPixmap:
            path = assets_dir / filename
            if path.exists():
                return QtGui.QPixmap(str(path))
            return QtGui.QPixmap()

        # Main logo at top of dock
        self.label_18.setPixmap(make_pixmap("Ctrl+IncisionLogo.png"))
        self.label_18.setScaledContents(True)

        # Step 1 – camera buttons
        self.imgCaptureButton.setIcon(
            make_icon("capture_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.png")
        )
        self.openCamSettingsButton.setIcon(
            make_icon("settings_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.png")
        )

        # Step 2 – tracking toggle
        self.trackerToggle.setIcon(
            make_icon("play_pause_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.png")
        )

        # Step 3 – pivot calibration toggle
        self.pivotToggle.setIcon(
            make_icon("adjust_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.png")
        )

        # Step 5 – intrinsic calibration run button
        self.runIntButton.setIcon(
            make_icon("play_arrow_24dp_1F1F1F_FILL0_wght400_GRAD0_opsz24.png")
        )

        self.label_21.setScaledContents(True)
        # ---------- end icon/logo fix ----------
        
        # --- Make the left-hand workflow panel scrollable ---
        self.scrollArea = QtWidgets.QScrollArea(self.dockWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)

        # dockWidgetContents was created by setupUi; we reparent it into the scroll area
        self.scrollArea.setWidget(self.dockWidgetContents)
        self.dockWidget.setWidget(self.scrollArea)
        # --- end scroll setup ---
        
        # Video widget setup
        self.overlay = OverlayApp(video_source, self)
        
        self.videoGridLayout.addWidget(self.overlay, 0, 0)

        # Tracker widget setup
        self.ren = vtk.vtkRenderer()
        self.qvtkwin = QVTKRenderWindowInteractor(self.trackerwidget)
        self.qvtkwin.GetRenderWindow().AddRenderer(self.ren)
        self.ren.SetBackground(.1, .2, .4)
        self.iren = self.qvtkwin.GetRenderWindow().GetInteractor()
        self.trackerGridLayout.addWidget(self.qvtkwin, 0, 0)

        # Tracker setup
        self.tracker = None
        self.trackerTimer = QtCore.QTimer()
        self.isTrackerInitialized = False
        self.trackerSettings = {}

        # Tracker widget status graphic setup
        self.logoWidgetX = 16
        self.logoWidgetY = 10
        self.trackerDrawing = vtk.vtkImageCanvasSource2D()
        self.trackerLogoWidget = vtk.vtkLogoWidget()
        self.trackerLogoRepresentation = vtk.vtkLogoRepresentation()

        # Tracked objects
        self.sphereSource = vtk.vtkSphereSource()
        self.sphereActor = vtk.vtkActor()
        self.sphereMapper = vtk.vtkPolyDataMapper()
        self.styTransform = vtk.vtkTransform()
        self.refTransform = vtk.vtkTransform()
        self.tipTransform = vtk.vtkTransform()
        self.camTransform = vtk.vtkTransform()

        # Image/data capture setup
        self.capture = False
        self.captureMsg = QtWidgets.QMessageBox()
        self.styTrackingCaptures = []
        self.camTrackingCaptures = []
        self.singleCaptureButton = self.captureMsg.addButton("Capture", QtWidgets.QMessageBox.ActionRole)
        self.captureSequenceIdx = 0
        self.captureSequenceDir = ""

        # Continuous capture (Start/Stop)
        self.contCaptureTimer = QtCore.QTimer()
        self.contCaptureTimer.timeout.connect(self._contCaptureTick)
        self.contCaptureActive = False
        self.contCaptureFrameIdx = 0
        self.contCaptureCsvFile = None
        self.contCaptureCsvWriter = None
        self.contCaptureStartWall = 0.0
        self.contCaptureStartMono = 0.0

        # Continuous capture buttons (separate from existing workflow)
        self.startContCaptureButton = QtWidgets.QPushButton("Start Continuous")
        self.stopContCaptureButton = QtWidgets.QPushButton("Stop Continuous")
        self.stopContCaptureButton.setEnabled(False)
        self.saveCaptureToDB = QtWidgets.QPushButton("Save Capture to DB")
        self.saveCaptureToDB.setEnabled(False)

        # --- DB setup ---
        init_db()

        # Register the current video source as the active device
        self.db_device_id = get_or_create_device(
            name="Dev Webcam",
            type="CAMERA",
            connection_info="OpenCV VideoCapture"
        )
        self.db_config_id = None
        self.db_capture_session_id = None
        self.db_last_capture_dir = None

        try:
            lay = self.startImgTrackerButton.parentWidget().layout()
            lay.addWidget(self.startContCaptureButton)
            lay.addWidget(self.stopContCaptureButton)
            lay.addWidget(self.saveCaptureToDB)
        except Exception:
            # Fallback: add to the dock contents layout so it's at least visible/usable
            if self.dockWidgetContents.layout() is not None:
                self.dockWidgetContents.layout().addWidget(self.startContCaptureButton)
                self.dockWidgetContents.layout().addWidget(self.stopContCaptureButton)
                self.dockWidgetContents.layout().addWidget(self.saveCaptureToDB)


        # Pivot calibration setup
        self.minimizer = vtk.vtkAmoebaMinimizer()
        self.pivotCalArray = vtk.vtkDoubleArray()
        self.pivotCalArray.SetNumberOfComponents(16)
        self.pivotCalMat = np.empty((4,4))
        self.appliedPivotCal = vtk.vtkTransform()
        self.loadedPivotCal = vtk.vtkTransform()
        self.collectPivotCalData = False
        self.stylusActor = vtk.vtkActor()

        # Visual calibration test object setup
        self.showHETest = False
        self.testSphereSource = vtk.vtkSphereSource()
        self.testSphereActor = vtk.vtkActor()
        self.testTransform = vtk.vtkTransform()
        self.testSphereMapper = vtk.vtkPolyDataMapper()
        self.overlayCamWidth = 0
        self.overlayCamHeight = 0

        # Calibration matrices
        self.extMatHE = np.eye(4)
        self.intMatHE = np.eye(3)
        self.distCoeffs = np.zeros((1, 5))

        # Other setup function calls
        self.setupVtkObjects()
        self.connectSignalsSlots()
        self.setQtDefaults()
         # Fake tracker setup (continuous synthetic data)
        self.fakeTracker = None
        self.fakeTrackerTimer = None

        
        if USE_FAKE_TRACKER:
            # Create and start the background fake tracker thread
            self.fakeTracker = FakeTracker(update_rate=0.05)
            self.fakeTracker.start()

            # Create and start the Qt timer that calls updateFakeTrackerInfo
            self.fakeTrackerTimer = QtCore.QTimer()
            self.fakeTrackerTimer.timeout.connect(self.updateFakeTrackerInfo)
            self.fakeTrackerTimer.start(50)  # 50 ms = 20 Hz

    def connectSignalsSlots(self):
        """Connects signals from Qt UI components with slot functions defined in this program"""

        # Browse buttons
        self.browseHEImageButton.clicked.connect(self.browseHEImage)
        self.browseHETrackingButton.clicked.connect(self.browseHETracking)
        self.browseChessButton.clicked.connect(self.browseChess)
        self.browseIntCalButton.clicked.connect(self.browseIntCal)
        self.browseStyROM.clicked.connect(self.browseStyROMClicked)
        self.browseCamROM.clicked.connect(self.browseCamROMClicked)

        # Capture and tracking
        self.imgCaptureButton.clicked.connect(self.captureFrame)
        self.openCamSettingsButton.clicked.connect(self.overlay.camera.open_settings)
        self.startImgTrackerButton.clicked.connect(self.startCaptureSeq)

        self.startContCaptureButton.clicked.connect(self.startContinuousCapture)
        self.stopContCaptureButton.clicked.connect(self.stopContinuousCapture)
        self.saveCaptureToDB.clicked.connect(self.saveCaptureToDatabase)

        # Running procedures
        self.runIntButton.clicked.connect(self.runIntCal)
        self.beginHEButton.clicked.connect(self.runHECal)
        self.testHEToggle.toggled.connect(self.handleTestHEToggle)
        self.saveHEButton.clicked.connect(self.saveHECal)
        self.loadHEButton.clicked.connect(self.loadHECal)
        
        # Pivot calibration
        self.browsePivotCalButton.clicked.connect(self.browsePivotCal)
        self.savePivotButton.clicked.connect(self.savePivotCal)
        self.applyPivotButton.clicked.connect(self.applyPivotCal)
        self.applyPivotFileButton.clicked.connect(self.applyPivotCal)

        # Toggles
        self.trackerToggle.toggled.connect(self.startTracker)
        self.pivotToggle.toggled.connect(self.handlePivotToggle)

        # Tracker source selector (UI-level only; FakeTracker remains the active source)
        if hasattr(self, "trackerSourceCombo"):
            self.trackerSourceCombo.currentIndexChanged.connect(self.handleTrackerSourceChanged)
    
    def handleTrackerSourceChanged(self, index: int) -> None:
        """
        Called when the user changes the tracker source combo box.
        For this sprint, we only log the choice; FakeTracker remains the active source.
        """
        if hasattr(self, "trackerSourceCombo"):
            text = self.trackerSourceCombo.currentText()
            self.log(f"Tracker source set to: {text}")


    def setupVtkObjects(self):
        """Initializes and connects VTK objects"""
        self.sphereSource.SetCenter(0, 0, 0)
        self.sphereSource.SetRadius(SPHERE_RADIUS)

        # Initialize all transforms to identity
        self.tipTransform.Identity()
        self.appliedPivotCal.Identity()
        self.refTransform.Identity()
        self.styTransform.Identity()
        self.testTransform.Identity()

        # Mapper/actor for tracked sphere
        self.sphereMapper.SetInputConnection(self.sphereSource.GetOutputPort())
        self.sphereActor.SetMapper(self.sphereMapper)

        # Transformation chain to get tip of stylus
        self.tipTransform.PostMultiply()
        self.tipTransform.Concatenate(self.appliedPivotCal)
        self.tipTransform.Concatenate(self.styTransform)
        self.tipTransform.Concatenate(self.camTransform.GetLinearInverse())
        
        # Mapper/actor for visual calibration test sphere
        self.testSphereSource.SetRadius(SPHERE_RADIUS)
        self.testSphereMapper.SetInputConnection(self.testSphereSource.GetOutputPort())
        self.testSphereActor.SetMapper(self.testSphereMapper)

    def log(self, message: str) -> None:
        """
        Append a message to the on-screen log (if present) and to the console.
        """
        text = str(message)

        # Write to the log pane in the UI if it exists
        if hasattr(self, "logConsole") and self.logConsole is not None:
            self.logConsole.appendPlainText(text)

        # Keep existing console behaviour
        print(text)

    def updateWorkflowStatus(self) -> None:
        """
        Update the small status labels and enable/disable the HE button
        based on the internal flags (_intcal_ok, _pivot_ok, _he_ok).
        """

        # --- Pivot status = LEFT label (statusIntCal) ---
        if hasattr(self, "statusIntCal"):
            if getattr(self, "_pivot_ok", False):
                self.statusIntCal.setText("Pivot: Applied")
                self.statusIntCal.setStyleSheet(
                    "background-color: #2e7d32; color: white;"
                )
            else:
                self.statusIntCal.setText("Pivot: Not applied")
                self.statusIntCal.setStyleSheet("")

        # --- Intrinsic status = MIDDLE label (statusPivot) ---
        if hasattr(self, "statusPivot"):
            if getattr(self, "_intcal_ok", False):
                self.statusPivot.setText("Intrinsic: Done")
                self.statusPivot.setStyleSheet(
                    "background-color: #2e7d32; color: white;"
                )
            else:
                self.statusPivot.setText("Intrinsic: Not run")
                self.statusPivot.setStyleSheet("")

        # --- Hand-eye status = RIGHT label (unchanged) ---
        if hasattr(self, "statusHE"):
            if getattr(self, "_he_ok", False):
                self.statusHE.setText("Hand-Eye: Solved")
                self.statusHE.setStyleSheet(
                    "background-color: #2e7d32; color: white;"
                )
            else:
                self.statusHE.setText("Hand-Eye: Not run")
                self.statusHE.setStyleSheet("")

        # Enable HE only after pivot + intrinsic are done
        if hasattr(self, "beginHEButton"):
            self.beginHEButton.setEnabled(
                getattr(self, "_intcal_ok", False)
                and getattr(self, "_pivot_ok", False)
            )


    
    def setQtDefaults(self):
        """Set default file names in fields and initialise workflow UI state."""

        # Buttons
        self.optTrackerRadio.setChecked(True)
        self.applyPivotFileButton.setEnabled(True)

        # Default field values
        self.numCapturesBox.setValue(12)

        self.styROMField.setText("GreenStylus.rom")
        self.camROMField.setText("LogitechDRB.rom")
        self.intCalField.setText("intcal.xml")
        self.findHEImageField.setText("sample_calibration_images")
        self.findHETrackingField.setText("sample_calibration_images/stylus_tracking_captures.xml")
        
        self.findPivotCalField.setText("pivotcal.xml")
        fname = self.findPivotCalField.text()
        self.pivotCalMat = cio.readPivotCalFromXml(fname)
        self.loadedPivotCal.SetMatrix(np.reshape(self.pivotCalMat, 16))

        # Tracker source combo default (for your Phone/Fake vs NDI concept)
        if hasattr(self, "trackerSourceCombo") and self.trackerSourceCombo.count() > 0:
            self.trackerSourceCombo.setCurrentIndex(0)

        # Workflow state flags for the status strip
        self._intcal_ok = False   # Intrinsic calibration done
        self._pivot_ok = False    # Pivot calibration applied
        self._he_ok = False       # Hand-eye calibration solved

        # Initialise the status labels and button enable/disable
        self.updateWorkflowStatus()

    
    def captureFrame(self):
        """ Sets capture flag to true so it can be handled by overlay widget class"""
        self.capture = True

    def browseStyROMClicked(self):
        """ Browsing window for stylus ROM file (optical tracking) """
        fname, d = QtWidgets.QFileDialog.getOpenFileName()
        self.styROMField.setText(fname)

    def browseCamROMClicked(self):
        """ Browsing window for camera ROM file (optical tracking) """
        fname, d = QtWidgets.QFileDialog.getOpenFileName()
        self.camROMField.setText(fname)
    
    def browseChess(self):
        """ Browsing window for chessboard image directory (intrinsic calibration)"""
        dir = QtWidgets.QFileDialog.getExistingDirectory()
        self.findChessField.setText(dir)

    def browsePivotCal(self):
        """ Browsing window for pivot calibration stored in XML file """
        fname, d = QtWidgets.QFileDialog.getOpenFileName()
        self.findPivotCalField.setText(fname)
        self.pivotCalMat = cio.readPivotCalFromXml(fname)
        self.loadedPivotCal.SetMatrix(np.reshape(self.pivotCalMat, 16))
        self.applyPivotFileButton.setEnabled(True)

    def browseHEImage(self):
        """ Browsing window for hand-eye calibration image directory """
        dir = QtWidgets.QFileDialog.getExistingDirectory()
        self.findHEImageField.setText(dir)

    def browseHETracking(self):
        """ Browsing window for hand-eye calibration tracking file """
        fname, d = QtWidgets.QFileDialog.getOpenFileName()
        self.findHETrackingField.setText(fname)

    def browseIntCal(self):
        """ Browsing window for intrinsic calibration stored in XML file """
        fname, d = QtWidgets.QFileDialog.getOpenFileName()
        self.intCalField.setText(fname)
        intmat, distcoeffs = cio.readIntCalFromXml(fname)

    def handleCapture(self, frame):
        if self.plusActive:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # for no transformation
            I16 = [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0
            ]

            self.plusFramesGray.append(gray)
            self.plusTimes.append(float(self._plusLastTime))

             # if probe valid
            if self._plusLastProbeValid:
                self.plusProbe16.append(self._plusLastProbe16)
            else:
                self.plusProbe16.append(I16)
            self.plusProbeValid.append(self._plusLastProbeValid)

            # if stylus valid
            if self._plusLastStylusValid:
                self.plusStylus16.append(self._plusLastStylus16)
            else:
                self.plusStylus16.append(I16)
            self.plusStylusValid.append(self._plusLastStylusValid)

            # if ref valid
            if self._plusLastRefValid:
                self.plusRef16.append(self._plusLastRef16)
            else:
                self.plusRef16.append(I16)
            self.plusRefValid.append(self._plusLastRefValid)

            return
    
        """ Receives screenshot as NumPy array and writes it to specified directory"""
        if self.captureSequenceIdx > 0:
            fname = f"{self.captureSequenceDir}/capture_{self.captureSequenceIdx}.png"
        else:
            fname, d = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", QtCore.QDir.currentPath(), "PNG (*.png)")
        cv2.imwrite(fname, frame)

        if self.contCaptureActive and self.contCaptureCsvWriter is not None:
            t_wall = time.time() - self.contCaptureStartWall
            t_mono = time.monotonic() - self.contCaptureStartMono
            self.contCaptureCsvWriter.writerow([
                self.contCaptureFrameIdx,
                os.path.basename(fname),
                f"{t_wall:.6f}",
                f"{t_mono:.6f}",
            ])
            self.contCaptureFrameIdx += 1

    def startCaptureSeq(self):
        """Starts sequence of capturing simultaneous image and tracking data."""

        numCaptures = self.numCapturesBox.value()

        # Let user choose where to save this capture set
        self.captureSequenceDir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Capture Output Directory"
        )
        if not self.captureSequenceDir:
            return  # user cancelled
        
        # ---- PLUS output file ----
        default_mha = os.path.join(self.captureSequenceDir, "TrackedSequence_.igs.mha")
        mha_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save PLUS Sequence (.igs.mha)",
            default_mha,
            "PLUS Sequence (*.igs.mha *.mha)"
        )
        if not mha_path:
            return  # user cancelled

        self.startPlusRecording(mha_path)
        # -------------------------------


        # Clear any previous captures in memory
        self.styTrackingCaptures = []
        self.camTrackingCaptures = []

        # Run the capture dialog numCaptures times
        for i in range(numCaptures):
            self.captureMsg.setText(
                f"Image and Tracking Data Capture #{i+1}\nPress Capture button when ready"
            )
            self.singleCaptureButton.disconnect(None, None, None)
            self.singleCaptureButton.clicked.connect(lambda _, idx=i: self.singleCapture(idx))
            self.captureMsg.exec()

        # Choose filenames depending on whether we're in fake or real tracker mode
        if USE_FAKE_TRACKER:
            sty_filename = "stylus_tracking_captures_fake.xml"
            cam_filename = "camera_tracking_captures_fake.xml"
        else:
            sty_filename = "stylus_tracking_captures.xml"
            cam_filename = "camera_tracking_captures.xml"

        # Write tracking captures to XML in the chosen folder
        sty_path = os.path.join(self.captureSequenceDir, sty_filename)
        cam_path = os.path.join(self.captureSequenceDir, cam_filename)

        cio.writeTrackingToXml(sty_path, self.styTrackingCaptures)
        cio.writeTrackingToXml(cam_path, self.camTrackingCaptures)

        # write PLUS file
        self.stopPlusRecording()

        self.captureSequenceIdx = 0

    def singleCapture(self, i):
        """Captures one image screenshot with corresponding tracking data"""
        self.captureSequenceIdx = i + 1
        if self.plusActive:
            self._snapshot_plus_metadata()
        # Screenshot
        self.captureFrame()

        progressDialog = QtWidgets.QProgressDialog("Collecting...", "Cancel", 0, NUM_TRACKING_FRAMES, self)
        progressDialog.setMinimumDuration(0)
        progressDialog.setWindowModality(QtCore.Qt.WindowModal)
        sty_pts = []
        sty_rotations = []
        cam_pts = []
        cam_rotations = []

        # Collects positional and rotational tracking data for camera and stylus over NUM_TRACKING_FRAMES
        for j in range(NUM_TRACKING_FRAMES):
            progressDialog.setValue(j)
            styPos = self.tipTransform.GetPosition()
            camPos = self.camTransform.GetPosition()
            if not np.isnan(np.sum(styPos)) and not np.isnan(np.sum(camPos)):
                sty_pts.append(styPos)
                cam_pts.append(camPos)
                styRotMat = self.tipTransform.GetMatrix()
                camRotMat = self.camTransform.GetMatrix()
                styRot = np.empty((9))
                camRot = np.empty((9))
                for k in range(3):
                   for l in range(3):
                       styRot[int(k*l+l)] = styRotMat.GetElement(k, l)
                       camRot[int(k*l+l)] = camRotMat.GetElement(k, l)
                sty_rotations.append(styRot)
                cam_rotations.append(camRot)
        progressDialog.setValue(NUM_TRACKING_FRAMES)
        sty_rotations = np.array(sty_rotations)
        cam_rotations = np.array(cam_rotations)

        # Averages 3D positional tracking data across NUM_TRACKING_FRAMES
        sty_avgPos = Stats.robustAverage3D(np.array(sty_pts))
        cam_avgPos = Stats.robustAverage3D(np.array(cam_pts))

        # Averages rotational tracking data across NUM_TRACKING_FRAMES
        sty_avgRot = np.empty((3, 3))
        cam_avgRot = np.empty((3, 3))
        for j in range(3):
            for k in range(3):
                sty_avgRot[j, k] = Stats.robustAverage1D(np.array(sty_rotations[:, int(k*j+k)]))
                cam_avgRot[j, k] = Stats.robustAverage1D(np.array(cam_rotations[:, int(k*j+k)]))

        # Adds stylus and camera tracking data to respective files
        self.styTrackingCaptures.append([sty_avgPos, sty_avgRot])
        self.camTrackingCaptures.append([cam_avgPos, cam_avgRot])
        self.captureMsg.accept()

    def startTracker(self):
        """Starts or stops tracker (real NDI or fake tracker depending on USE_FAKE_TRACKER)."""

        # Toggle ON
        if self.trackerToggle.isChecked():

            # -------- FAKE TRACKER MODE --------
            if USE_FAKE_TRACKER:

                if self.fakeTracker is None:
                    self.fakeTracker = FakeTracker(update_rate=0.05)

                self.fakeTracker.start()

                if self.fakeTrackerTimer is None:
                    self.fakeTrackerTimer = QtCore.QTimer()
                    self.fakeTrackerTimer.timeout.connect(self.updateFakeTrackerInfo)

                # run at 20 Hz
                self.fakeTrackerTimer.start(50)
                
                 # Mark tracker as initialized so pivot logic can run
                self.isTrackerInitialized = True
                print("Fake tracker initialized.")

                # Show the tracked sphere
                self.sphereActor.SetUserTransform(self.tipTransform)
                self.ren.AddActor(self.sphereActor)
                self.ren.ResetCamera()
                self.qvtkwin.GetRenderWindow().Render()
                return  # IMPORTANT: do NOT fall through to real NDI code

            # -------- REAL NDI TRACKER MODE (original behavior) --------
            if not self.isTrackerInitialized:
                try:
                    if self.magTrackerRadio.isChecked():
                        self.trackerSettings = {
                            "tracker type": "aurora",
                            "ports to probe": NUM_PORTS,
                            "verbose": True
                        }
                    elif self.optTrackerRadio.isChecked():
                        self.trackerSettings = {
                            "tracker type": "polaris",
                            "romfiles": [self.styROMField.text(), self.camROMField.text()]
                        }
                    self.tracker = NDITracker(self.trackerSettings)
                    self.isTrackerInitialized = True
                    self.tracker.use_quaternions = False

                    self.sphereActor.SetUserTransform(self.tipTransform)
                    self.trackerTimer.timeout.connect(self.updateTrackerInfo)
                except Exception as e:
                    print("Unable to connect to NDI Tracker device:", e)
                    self.isTrackerInitialized = False
                    self.trackerToggle.setChecked(False)

            if self.isTrackerInitialized:
                self.tracker.start_tracking()
                self.trackerTimer.start(0)
                self.createTrackerLogo()
                self.trackerLogoWidget.On()
                self.ren.AddActor(self.sphereActor)
                self.qvtkwin.GetRenderWindow().Render()

        # Toggle OFF
        else:

            # -------- FAKE TRACKER MODE --------
            if USE_FAKE_TRACKER:
                if self.fakeTrackerTimer is not None:
                    self.fakeTrackerTimer.stop()
                if self.fakeTracker is not None:
                    self.fakeTracker.stop()
                    
                self.isTrackerInitialized = False
                self.collectPivotCalData = False
                print("Fake tracker stopped.")

                self.ren.RemoveActor(self.sphereActor)
                self.qvtkwin.GetRenderWindow().Render()
                return  # IMPORTANT: do NOT fall through to real NDI code

            # -------- REAL NDI TRACKER MODE --------
            if self.isTrackerInitialized:
                self.trackerTimer.stop()
                self.tracker.stop_tracking()
                self.trackerLogoWidget.Off()
                self.ren.RemoveActor(self.sphereActor)
                self.ren.RemoveActor(self.stylusActor)
                self.qvtkwin.GetRenderWindow().Render()

    def updateTrackerInfo(self):
        """
        Updates VTK objects, error display, and volume display with new tracking information (called as often as possible)
        """
        if self.isTrackerInitialized:
            port_handles, time_stamps, frame_numbers, tracking, tracking_quality = self.tracker.get_frame()

            sty_mat = tracking[PORT_STYLUS]
            sty_mat_16 = np.reshape(sty_mat, 16)

            cam_mat = tracking[PORT_CAMERA]
            cam_mat_16 = np.reshape(cam_mat, 16)

            if self.collectPivotCalData and not np.isnan(np.sum(sty_mat_16) + np.sum(cam_mat_16)):
                self.pivotCalArray.InsertNextTuple(sty_mat_16)
                
                count = self.pivotCalArray.GetNumberOfTuples()
                if count == 1:
                    print("First pivot sample collected.")
                if count % 10 == 0:
                    print("Pivot samples collected so far:", count)
            
            self.styTransform.SetMatrix(sty_mat_16)
            self.camTransform.SetMatrix(cam_mat_16)

            self.tipTransform.Update()

            # if testing HE calibration, update transform of overlayed sphere
            if self.showHETest:

                tipMat = self.tipTransform.GetMatrix()
                pt = np.ones((4, 1))
                pt[0, 0] = tipMat.GetElement(0, 3)
                pt[1, 0] = tipMat.GetElement(1, 3)
                pt[2, 0] = tipMat.GetElement(2, 3)
                camPt = np.linalg.inv(self.extMatHE) @ pt

                self.testTransform.Update()
                
                m = self.testSphereActor.GetUserTransform().GetMatrix()
                mx = m.GetElement(0, 3) 
                my = m.GetElement(1, 3)
                mz = m.GetElement(2, 3)

                self.overlay.vtk_overlay_window.foreground_renderer.ResetCameraClippingRange()
                self.overlay.vtk_overlay_window.GetRenderWindow().Render()


            self.updateVolumeDisplay(tracking)
            self.updateTrackingPositions()
            self.updateErrorDisplay(tracking_quality)

            self.ren.ResetCameraClippingRange()
            self.qvtkwin.GetRenderWindow().Render()
    def updateFakeTrackerInfo(self):
        """
        Uses FakeTracker data to update BOTH stylus and camera positions and GUI.
        Runs continuously via fakeTrackerTimer.
        """
        if not USE_FAKE_TRACKER or self.fakeTracker is None:
            return

        if self.qvtkwin is None or not self.qvtkwin.isVisible():
            return

        rw = self.qvtkwin.GetRenderWindow()
        if rw is None:
            return

    # Get full fake stylus pose (pivot-like transform)
        sty_mat = self.fakeTracker.get_stylus_matrix()

    # Keep camera fixed for pivot testing
        cam_mat = np.eye(4)
        cam_mat[0:3, 3] = [0.0, 0.0, 0.0]

    # Convert to VTK 4x4 format
        sty_mat_16 = np.reshape(sty_mat, 16)
        cam_mat_16 = np.reshape(cam_mat, 16)

        if self.collectPivotCalData and not np.isnan(np.sum(sty_mat_16) + np.sum(cam_mat_16)):
            self.pivotCalArray.InsertNextTuple(sty_mat_16)

            count = self.pivotCalArray.GetNumberOfTuples()
            if count == 1:
                print("First fake-tracker pivot sample collected.")
            if count % 10 == 0:
                print("Fake-tracker pivot samples collected so far:", count)

    # Feed into the same transforms the real tracker would use
        self.styTransform.SetMatrix(sty_mat_16)
        self.camTransform.SetMatrix(cam_mat_16)

    # Update tip transform chain
        self.tipTransform.Update()

    # if testing HE calibration, update transform of overlayed sphere
        if self.showHETest:

            tipMat = self.tipTransform.GetMatrix()
            pt = np.ones((4, 1))
            pt[0, 0] = tipMat.GetElement(0, 3)
            pt[1, 0] = tipMat.GetElement(1, 3)
            pt[2, 0] = tipMat.GetElement(2, 3)
            camPt = np.linalg.inv(self.extMatHE) @ pt

            self.testTransform.Update()

            m = self.testSphereActor.GetUserTransform().GetMatrix()
            mx = m.GetElement(0, 3)
            my = m.GetElement(1, 3)
            mz = m.GetElement(2, 3)

            self.overlay.vtk_overlay_window.foreground_renderer.ResetCameraClippingRange()
            self.overlay.vtk_overlay_window.GetRenderWindow().Render()

    # Update GUI LCDs
        self.updateTrackingPositions()

        self.ren.ResetCameraClippingRange()
        self.qvtkwin.GetRenderWindow().Render()

    def createTrackerLogo(self):
        """Initializes rectangular icons showing tracked tool status (red = not tracking, green = tracking)"""

        n = NUM_PORTS
        self.trackerDrawing.SetScalarTypeToUnsignedChar()
        self.trackerDrawing.SetNumberOfScalarComponents(3)
        self.trackerDrawing.SetExtent(0, self.logoWidgetX*n + n, 0, self.logoWidgetY + 2, 0, 0)
        self.trackerDrawing.SetDrawColor(255, 255, 255)
        self.trackerDrawing.FillBox(0, self.logoWidgetX*n + n, 0, self.logoWidgetY + 2)

        self.trackerDrawing.Update()
        self.trackerLogoRepresentation.SetImage(self.trackerDrawing.GetOutput())
        self.trackerLogoRepresentation.SetPosition(0.45, 0)
        self.trackerLogoRepresentation.SetPosition2(0.1, 0.1)
        self.trackerLogoRepresentation.GetImageProperty().SetOpacity(0.5)
        
        self.trackerLogoWidget.SetRepresentation(self.trackerLogoRepresentation)
        self.trackerLogoWidget.SetInteractor(self.iren)

    def updateVolumeDisplay(self, tracking):
        """Updates rectangular icons showing tracked tool status (red = not tracking, green = tracking)"""
        for i, trackingInfo in enumerate(tracking):
            if np.isnan(np.sum(trackingInfo)):
                self.trackerDrawing.SetDrawColor(255, 0, 0)
                self.trackerDrawing.FillBox(self.logoWidgetX*i + i + 1, self.logoWidgetX*(i + 1) + i, 1, self.logoWidgetY + 1)
            else:
                self.trackerDrawing.SetDrawColor(0, 255, 0)
                self.trackerDrawing.FillBox(self.logoWidgetX*i + i + 1, self.logoWidgetX*(i + 1) + i, 1, self.logoWidgetY + 1)
                
        self.trackerDrawing.Update()

    def updateErrorDisplay(self, tracking_quality):
        """Updates error LCD such that background is green for values below ERROR_THRESHOLD and red otherwise"""
        styErr = tracking_quality[PORT_STYLUS]
        camErr = tracking_quality[PORT_CAMERA]

        camPalette = self.camErr.palette()
        if camErr < ERROR_THRESHOLD:
            camPalette.setColor(self.camErr.backgroundRole(), QtGui.QColor(QtCore.Qt.GlobalColor.green))
        else:
            camPalette.setColor(self.camErr.backgroundRole(), QtGui.QColor(QtCore.Qt.GlobalColor.red))
            
        styPalette = self.styErr.palette()
        if styErr < ERROR_THRESHOLD:
            styPalette.setColor(self.styErr.backgroundRole(), QtGui.QColor(QtCore.Qt.GlobalColor.green))
        else:
            styPalette.setColor(self.styErr.backgroundRole(), QtGui.QColor(QtCore.Qt.GlobalColor.red))
            
        self.camErr.setPalette(camPalette)
        self.styErr.setPalette(styPalette)
        self.camErr.display(camErr)
        self.styErr.display(styErr)
    
    def updateTrackingPositions(self):
        """Updates LCDs with x, y, z coordinates of both tools from tracker"""
        camPos = self.camTransform.GetPosition()
        self.camTx.display(camPos[0])
        self.camTy.display(camPos[1])
        self.camTz.display(camPos[2])

        styPos = self.tipTransform.GetPosition()
        self.styTx.display(styPos[0])
        self.styTy.display(styPos[1])
        self.styTz.display(styPos[2])

    def minimizerFunc(self):
        """Runs AmoebaMinimizer on pivot calibration tracking data"""
        n = self.pivotCalArray.GetNumberOfTuples()
        x = self.minimizer.GetParameterValue("x")
        y = self.minimizer.GetParameterValue("y")
        z = self.minimizer.GetParameterValue("z")

        #mat = np.empty((4, 4))
        sx = sy = sz = 0.0
        sxx = syy = szz = 0.0

        for i in range(n):
            mat = self.pivotCalArray.GetTuple(i)
            mat = np.reshape(mat, (4,4))
            nx = mat[0,0]*x + mat[0,1]*y + mat[0,2]*z + mat[0,3]
            ny = mat[1,0]*x + mat[1,1]*y + mat[1,2]*z + mat[1,3]
            nz = mat[2,0]*x + mat[2,1]*y + mat[2,2]*z + mat[2,3]

            sx += nx
            sy += ny
            sz += nz

            sxx += nx*nx
            syy += ny*ny
            szz += nz*nz

        if n > 1:
            r = np.sqrt((sxx - sx*sx/n)/(n - 1) + (syy - sy*sy/n)/(n - 1) + (szz - sz*sz/n)/(n - 1))
        else:
            r = 0.0

        self.minimizer.SetFunctionValue(r)
    
    def doPivotCal(self):
        """Sets parameters and calls minimizer function for pivot calibration"""
        print("Entered doPivotCal()")
        print("Samples available for pivot solve:", self.pivotCalArray.GetNumberOfTuples())
        self.pivotCalMat = np.eye(4)
        
        self.minimizer.SetFunction(self.minimizerFunc)

        self.minimizer.SetParameterValue("x", 0)
        self.minimizer.SetParameterScale("x", 1000)

        self.minimizer.SetParameterValue("y", 0)
        self.minimizer.SetParameterScale("y", 1000)

        self.minimizer.SetParameterValue("z", 0)
        self.minimizer.SetParameterScale("z", 1000)

        self.minimizer.Minimize()
        minimum = self.minimizer.GetFunctionValue()
        
        print("Pivot minimization finished.")
        print("Pivot residual / minimum error:", minimum)

        self.pivotCalMat[0, 3] = self.minimizer.GetParameterValue("x")
        self.pivotCalMat[1, 3] = self.minimizer.GetParameterValue("y")
        self.pivotCalMat[2, 3] = self.minimizer.GetParameterValue("z")
        
        print("Computed pivot calibration matrix:")
        print(self.pivotCalMat)
        print(
        "Computed pivot offset [x, y, z]:",
        self.pivotCalMat[0, 3],
        self.pivotCalMat[1, 3],
        self.pivotCalMat[2, 3]
    )

        self.pivotLcd.display(minimum)
        self.loadedPivotCal.SetMatrix(np.reshape(self.pivotCalMat, 16))
        
        print("Loaded pivot calibration transform updated.")

    def applyPivotCal(self):
        """
        Applies pivot calibration to the stylus transform and creates the VTK stylus actor.
        Called either after a live pivot calibration or when loading from an XML file.
        """
        print("Applying pivot calibration...")
        print("Loaded pivot calibration matrix before apply:")
        print(np.array(self.loadedPivotCal.GetMatrix()))
        
        # Copy loaded pivot transform into the applied one
        self.appliedPivotCal.SetMatrix(self.loadedPivotCal.GetMatrix())
        
        print("Applied pivot calibration matrix:")
        print(np.array(self.appliedPivotCal.GetMatrix()))

        # Create the stylus visual in the VTK scene (mode 2 = calibrated stylus)
        self.createStylusActor(2)

        # Update workflow state & UI
        self._pivot_ok = True
        self.updateWorkflowStatus()
        self.log("Pivot calibration applied.")
        print("Applied pivot calibration matrix:")
        print(np.array(self.appliedPivotCal.GetMatrix()))


    def handlePivotToggle(self):
        """Handles toggle for pivot calibration data collection"""
        print("handlePivotToggle() called")
        print("Tracker initialized:", self.isTrackerInitialized)
        
        if self.isTrackerInitialized:
            if self.pivotToggle.isChecked():
                print("Pivot collection started.")
                print("Existing pivot samples before reset:", self.pivotCalArray.GetNumberOfTuples())

                self.pivotCalArray.Initialize()
                self.pivotCalArray.SetNumberOfTuples(0)
                self.collectPivotCalData = True
                self.savePivotButton.setEnabled(False)
                self.applyPivotButton.setEnabled(False)
                print("Pivot sample buffer reset.")
                print("collectPivotCalData =", self.collectPivotCalData)
            
            else:
                print("Pivot collection stopped.")
                self.collectPivotCalData = False
                print("collectPivotCalData =", self.collectPivotCalData)
                print("Collected pivot samples:", self.pivotCalArray.GetNumberOfTuples())
                print("Running pivot calibration now...")
                self.doPivotCal()
                self.savePivotButton.setEnabled(True)
                self.applyPivotButton.setEnabled(True)
        else:
            print("Tracker not initialized. Pivot collection not started.")
            self.pivotToggle.setChecked(False)
    
    def savePivotCal(self):
        """Writes pivot calibration matrix to XML file"""
        fname, d = QtWidgets.QFileDialog.getSaveFileName(self, "Save XML File", QtCore.QDir.currentPath(), "XML Files (*.xml)")
        cio.writePivotCalToXml(fname, self.loadedPivotCal)

    def createStylusActor(self, dim):
        """Creates VTK object representation of stylus (after pivot calibration)"""
        pos = np.array([0, 0, 0, 1])
        pos[dim] = -1.0
        outpos = np.matmul(self.pivotCalMat, pos)
        pos = outpos/np.linalg.norm(outpos)

        append = vtk.vtkAppendPolyData()
        coneHeight = 25.0
        needleHeight = 150.0
        radius = 1.5
        nSides = 36
        
        line = vtk.vtkLineSource()
        line.SetPoint1(pos[0], pos[1], pos[2])
        line.SetPoint2(outpos[0], outpos[1], outpos[2])

        tube = vtk.vtkTubeFilter()
        tube.SetInputConnection(line.GetOutputPort())
        tube.SetRadius(radius)
        tube.SetNumberOfSides(nSides)

        cone = vtk.vtkConeSource()
        cone.SetHeight(coneHeight)
        cone.SetRadius(radius)
        cone.SetDirection(-pos[0], -pos[1], -pos[2])
        cone.SetResolution(nSides)
        cone.SetCenter(0.5*coneHeight*pos[0], 0.5*coneHeight*pos[1], 0.5*coneHeight*pos[2])

        append.AddInputConnection(tube.GetOutputPort())
        append.AddInputConnection(cone.GetOutputPort())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(append.GetOutputPort())
        self.stylusActor.SetMapper(mapper)
        self.stylusActor.SetUserTransform(self.tipTransform)

        self.ren.AddActor(self.stylusActor)

    def runIntCal(self):
        """Runs intrinsic calibration on a set of chessboard images using OpenCV."""
        dir_str = self.findChessField.text()

        if not dir_str:
            err = QtWidgets.QErrorMessage()
            err.showMessage('Folder holding calibration chessboard images must be provided!')
            return

        if not os.path.isdir(dir_str):
            err = QtWidgets.QErrorMessage()
            err.showMessage('Selected chessboard directory does not exist.')
            return

        # Collect image files
        image_files = []
        for name in sorted(os.listdir(dir_str)):
            lower = name.lower()
            if lower.endswith('.png') or lower.endswith('.jpg') or lower.endswith('.jpeg') or lower.endswith('.bmp'):
                image_files.append(os.path.join(dir_str, name))

        if not image_files:
            err = QtWidgets.QErrorMessage()
            err.showMessage('No .png/.jpg/.bmp images found in the selected folder.')
            return

        self.log(f"Running intrinsic calibration on {len(image_files)} images...")

        # Run OpenCV-based intrinsic calibration
        intMat, distCoeffs = he.distortionCalibration(image_files)

        # Ask where to save the result
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Intrinsic Calibration",
            QtCore.QDir.currentPath(),
            "XML Files (*.xml)",
        )
        if fname:
            cio.writeIntCalToXml(fname, intMat, distCoeffs)
            self.intCalField.setText(fname)
            self.log(f"Saved intrinsic calibration to {fname}")
        else:
            self.log("Intrinsic calibration computed but not saved to file.")

        # Tell the overlay about the new camera matrix
        self.overlay.set_camera_matrix(intMat, distCoeffs)

        # Update workflow state & UI
        self._intcal_ok = True
        self.updateWorkflowStatus()
        self.log("Intrinsic calibration completed.")

    
    def saveHECal(self):
        """Writes intrinsic matrix, distortion coefficients, and extrinsic matrix to XML file"""
        fname, d = QtWidgets.QFileDialog.getSaveFileName(self, "Save XML File", QtCore.QDir.currentPath(), "XML Files (*.xml)")
        cio.writeHECalToXml(fname, self.intMatHE, self.distCoeffs, self.extMatHE)
    
    def runHECal(self):
        """Runs hand-eye calibration based on point-to-line registration"""

        # Collects captured images from given folder
        frames_dir_str = self.findHEImageField.text()
        frames_dir = os.fsencode(frames_dir_str)
        imageFiles = []
        file_ctr = 0
        for file in os.listdir(frames_dir):
            file_str = os.fsdecode(file)
            if file_str.endswith('.png'):
                file_ctr += 1
                imageFiles.append(f"{frames_dir_str}/capture_{file_ctr}.png")

        # Reads tracking data corresponding to calibration images
        fname = self.findHETrackingField.text()
        trackingPositions, trackingRotations = cio.readTrackingFromXml(fname)

        # Reads intrinsic calibration
        intCalFile = self.intCalField.text()
        intMat, distCoeffs = cio.readIntCalFromXml(intCalFile)
        
        # Calls registration to get extrinsic matrix, reprojection coordinates, and error values
        extMat, px, pxErrs, distErrs, angularErrs = he.analyzeFrames(imageFiles, trackingPositions, intMat, distCoeffs)

        print("\n")
        print("Pixels")
        print(px)
        
        print("\n")
        print("Pixel error")
        print(pxErrs)
        print(f"Average pixel error: {np.sum(pxErrs)/len(pxErrs)} px")

        print("\n")
        print("Distance error")
        print(distErrs)
        print(f"Average distance error: {np.sum(distErrs)/len(distErrs)} mm")

        print("\n")
        print("Angular error")
        print(angularErrs)
        print(f"Average angular error: {np.sum(angularErrs)/len(angularErrs)} deg")

        # Displays and saves images with centroid reprojection
        output_path = f"{frames_dir_str}/output"
        os.makedirs(output_path, exist_ok=True)
        for i in range(len(px)):
            try:
                img = cv2.imread(f"{frames_dir_str}/capture_{i+1}.png")
                h, w = img.shape[:2]
                newCamMat, roi = cv2.getOptimalNewCameraMatrix(intMat, distCoeffs, (w, h), 1, (w, h))
                img = cv2.undistort(img, intMat, distCoeffs, None, newCamMat)
                if px[i][0, 0] != -1:
                    pxx = np.uint16(np.round(px[i][0, 0]))
                    pxy = np.uint16(np.round(px[i][1, 0]))
                    cv2.circle(img, (pxx, pxy), 1, (0, 255, 255), 2)
                    cv2.imwrite(f"{output_path}/reprojection_{i+1}.png", img)
            except:
                print("could not draw pixel onto image")

        # Writes error values to CSV file
        cio.writeErrToCsv(pxErrs, distErrs, angularErrs, output_path)

        self.extMatHE = extMat
        self.intMatHE = intMat
        self.distCoeffs = distCoeffs

        # Tell the overlay to use the HE-calibrated matrix
        self.overlay.set_camera_matrix(self.intMatHE, self.distCoeffs)

        # Update workflow state & UI
        self._he_ok = True
        self.updateWorkflowStatus()
        self.log("Hand-eye calibration completed.")

        self.testHEToggle.setEnabled(True)
        self.saveHEButton.setEnabled(True)
        cv2.destroyAllWindows()


    def loadHECal(self):
        """Loads hand-eye calibration (intrinsic matrix, distortion coefficients, and extrinsic matrix) from XML file"""
        fname, d = QtWidgets.QFileDialog.getOpenFileName()
        intMat, distCoeffs, extMat = cio.readHECalibrationFromXml(fname)
        self.intMatHE = intMat
        self.extMatHE = extMat
        self.distCoeffs = distCoeffs
        self.overlay.set_camera_matrix(self.intMatHE, self.distCoeffs)
        print("int mat", self.intMatHE)
        print("dist coeffs", self.distCoeffs)
        print("ext mat", self.extMatHE)
        # Loading a full HE calibration also implies intrinsic + HE are ready
        self._intcal_ok = True
        self._he_ok = True
        self.updateWorkflowStatus()
        self.log("Hand-eye calibration loaded from file.")

        self.testHEToggle.setEnabled(True)

    def handleTestHEToggle(self):
        """Handles toggle of AR overlay"""
        if self.testHEToggle.isChecked():
            # create overlay object
            self.showHETest = True
            
            w = self.overlay.width()
            h = self.overlay.height()
            print("width:", w)
            print("height:", h)

            extMatVTK = vtk.vtkTransform()
            extMatVTK.SetMatrix(np.reshape(self.extMatHE, 16))
            self.testTransform.PostMultiply()
            self.testTransform.Identity()
            self.testTransform.Concatenate(self.tipTransform)
            self.testTransform.Concatenate(extMatVTK)
            self.testSphereActor.SetUserTransform(self.testTransform)
            self.overlay.vtk_overlay_window.add_vtk_actor(self.testSphereActor)
            # set up vtk overlay camera
            vtkcam = self.overlay.vtk_overlay_window.foreground_renderer.GetActiveCamera()
            
            vtkcam.SetParallelProjection(False)
            vtkcam.SetPosition(0, 0, 0)
            vtkcam.SetFocalPoint(0, 0, 1)
            vtkcam.SetViewUp(0, -1, 0)

            cx = self.intMatHE[0, 2]
            cy = self.intMatHE[1, 2]
            fx = self.intMatHE[0, 0]
            print("cx:", cx)
            print("cy:", cy)
            wcx = -2 * (cx - float(w) / 2) / w
            wcy = 2 * (cy - float(h) / 2) / h
            vtkcam.SetWindowCenter(wcx, wcy)
            print("wcx:", wcx)
            print("wcy:", wcy)

            view_angle = 180 / np.pi * (2.0 * np.arctan2(h / 2.0, fx))
            print("view angle:", view_angle)
            vtkcam.SetViewAngle(view_angle)

        else:
            self.showHETest = False
            self.overlay.vtk_overlay_window.get_foreground_renderer().RemoveActor(self.testSphereActor)
                
    # ArUco → Stylus tracking integration 
    
    def updateArucoPose(self, T):
        """
        Receives 4x4 ArUco pose (marker -> camera)
        Updates stylus transform so VTK + overlay stay in sync
        """
        import numpy as np

        T = np.array(T).reshape(4, 4)

        # Update stylus transform
        self.styTransform.SetMatrix(np.reshape(T, 16))

        # Camera is reference frame (identity)
        cam_T = np.eye(4)
        self.camTransform.SetMatrix(np.reshape(cam_T, 16))

        # Update derived transforms
        self.tipTransform.Update()
        self.updateTrackingPositions()

        # Force render update
        self.qvtkwin.GetRenderWindow().Render()

    def getStylusTipInCameraFrame(self, T):
        """
        Returns stylus tip (XYZ) in camera coordinates
        Used for drawing overlay shapes
        """
        import numpy as np

        if self.appliedPivotCal is None:
            return None

        # Extract pivot offset from pivot calibration
        M = self.appliedPivotCal.GetMatrix()
        pivot = np.array([
            M.GetElement(0, 3),
            M.GetElement(1, 3),
            M.GetElement(2, 3),
            1.0
        ],dtype=float)
        
        pivot[:3] /= 1000.0   # mm -> meters
        pivot[:3] *= -1.0 

        T = np.array(T, dtype = float).reshape(4, 4)
        tip_cam = T @ pivot

        return tip_cam[:3]

    def startPlusRecording(self, out_path: str):
        """Buffer the frames and transforms for PLUS .igs.mha sequence"""
        self.plusActive = True
        self.plusOutPath = out_path
        self.plusT0 = time.monotonic()

        self.plusFramesGray = []
        self.plusTimes = []
        self.plusProbe16 = []
        self.plusStylus16 = []
        self.plusRef16 = []

    def stopPlusRecording(self):
        """Write buffered PLUS .igs.mha sequence"""
        if not self.plusActive:
            return
        self.plusActive = False

        if not self.plusOutPath or len(self.plusFramesGray) == 0:
            return
        
        n = len(self.plusFramesGray)
        h, w = self.plusFramesGray[0].shape  # grayscale uint8 => 1 byte/pixel
        raw_size = w * h * n                 # bytes (MET_UCHAR)
        compress_flag = raw_size > 20_000_000  # > ~20MB


        self._write_plus_sequence_mha(
            self.plusOutPath,
            self.plusFramesGray,
            self.plusTimes,
            self.plusProbe16,
            self.plusStylus16,
            self.plusRef16,
            self.plusProbeValid,
            self.plusStylusValid,
            self.plusRefValid,
            anatomical_orientation="RAI",
            ultrasound_image_orientation="MFA",
            compress=compress_flag,
            compress_level=6,
        )

        # --- DB: Register this .mha file as a captured ultrasound stream ---
        if self.plusOutPath and os.path.isfile(self.plusOutPath):
            session_id = self.db_capture_session_id or start_capture_session(
                device_id=self.db_device_id,
                config_id=self.db_config_id,
                output_dir=str(Path(self.plusOutPath).parent),
                fps=0.0,
                status="SAVED",
            )
            artifact_id = add_ultrasound_stream(
                session_id=session_id,
                file_path=self.plusOutPath,
                stream_type="MHA",
            )
            log_event(session_id, "MHA_SAVED", "INFO", f"artifact_id={artifact_id}, path={self.plusOutPath}")
            self.log(f"[DB] .mha registered → artifact_id={artifact_id}")
            self.saveCaptureToDB.setEnabled(True)
        else:
            self.log("[DB] WARNING: .mha file not found after write, skipping DB registration")

    def _snapshot_plus_metadata(self):
        """Transform and timestamp before requesting a capture frame"""
        self._plusLastTime = time.monotonic() - self.plusT0 # timestamp
        
        def vtk_to_16_if_valid(t):
            if t is None:
                return None, False

            m = t.GetMatrix()
            out = []
            for r in range(4):
                for c in range(4):
                    val = float(m.GetElement(r, c))
                    if np.isnan(val):
                        return None, False
                    out.append(val)
            return out, True

        self._plusLastProbe16, self._plusLastProbeValid = vtk_to_16_if_valid(self.camTransform)
        self._plusLastStylus16, self._plusLastStylusValid = vtk_to_16_if_valid(self.styTransform)
        self._plusLastRef16, self._plusLastRefValid = vtk_to_16_if_valid(self.refTransform)
        
    def _write_plus_sequence_mha(
        self,
        out_path: str,
        frames_gray: list,
        timestamps: list,
        probe16_list: list,
        stylus16_list: list,
        ref16_list: list,
        probe_valid_list: list,
        stylus_valid_list: list,
        ref_valid_list: list,
        anatomical_orientation="RAI",
        ultrasound_image_orientation="MFA",
        compress: bool = False,
        compress_level: int = 6,
    ):
        if not frames_gray:
            raise RuntimeError("No frames to write.")

        n = len(frames_gray)
        h, w = frames_gray[0].shape

        vol = np.stack(frames_gray, axis=0).astype(np.uint8)  # (N,H,W)
        raw_bytes = vol.tobytes(order="C")

        if compress:
            comp_bytes = zlib.compress(raw_bytes, level=compress_level)
            data_bytes = comp_bytes
            compressed_size = len(comp_bytes)
        else:
            data_bytes = raw_bytes
            compressed_size = None

        def mat16_str(m16):
            return " ".join(f"{float(x):.6g}" for x in m16)

        header = []
        header.append("ObjectType = Image\n")
        header.append("NDims = 3\n")
        header.append(f"AnatomicalOrientation = {anatomical_orientation}\n")
        header.append("BinaryData = True\n")
        header.append("BinaryDataByteOrderMSB = False\n")
        header.append("CenterOfRotation = 0 0 0\n")

        if compress:
            header.append("CompressedData = True\n")
            header.append(f"CompressedDataSize = {compressed_size}\n")
        else:
            header.append("CompressedData = False\n")

        header.append(f"DimSize = {w} {h} {n}\n")
        header.append("Kinds = domain domain list\n")
        header.append("ElementSpacing = 1 1 1\n")
        header.append("ElementType = MET_UCHAR\n")
        header.append("Offset = 0 0 0\n")
        header.append("TransformMatrix = 1 0 0 0 1 0 0 0 1\n")
        header.append(f"UltrasoundImageOrientation = {ultrasound_image_orientation}\n")

        for i in range(n):
            idx = f"{i:04d}"

            probe_status = "OK" if probe_valid_list[i] else "INVALID"
            stylus_status = "OK" if stylus_valid_list[i] else "INVALID"
            ref_status = "OK" if ref_valid_list[i] else "INVALID"

            header.append(f"Seq_Frame{idx}_ProbeToTrackerTransform = {mat16_str(probe16_list[i])}\n")
            header.append(f"Seq_Frame{idx}_ProbeToTrackerTransformStatus = {probe_status}\n")

            header.append(f"Seq_Frame{idx}_ReferenceToTrackerTransform = {mat16_str(ref16_list[i])}\n")
            header.append(f"Seq_Frame{idx}_ReferenceToTrackerTransformStatus = {ref_status}\n")

            header.append(f"Seq_Frame{idx}_StylusToTrackerTransform = {mat16_str(stylus16_list[i])}\n")
            header.append(f"Seq_Frame{idx}_StylusToTrackerTransformStatus = {stylus_status}\n")

            header.append(f"Seq_Frame{idx}_Timestamp = {float(timestamps[i]):.6f}\n")
            header.append("Seq_Frame%04d_ImageStatus = OK\n" % i) # alr checked for frame and dims

        header.append("ElementDataFile = LOCAL\n")

        with open(out_path, "wb") as f:
            f.write("".join(header).encode("ascii"))
            f.write(data_bytes)


    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super().closeEvent(event)

        # Stop fake tracker stuff first (if in fake mode)
        if USE_FAKE_TRACKER:
            if self.fakeTrackerTimer is not None:
                self.fakeTrackerTimer.stop()
            if self.fakeTracker is not None:
                self.fakeTracker.stop()

        # Then clean up VTK + overlay
        self.qvtkwin.close()
        self.qvtkwin.Finalize()
        self.overlay.close()

    def startContinuousCapture(self):
        if self.contCaptureActive:
            return

        out_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Continuous Capture Output Directory"
        )
        if not out_dir:
            return

        fps, ok = QtWidgets.QInputDialog.getDouble(
            self,
            "Continuous Capture FPS",
            "Frames per second:",
            20.0,   # value
            1.0,    # minValue
            60.0,   # maxValue
            1       # decimals
        )

        if not ok:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.captureSequenceDir = os.path.join(out_dir, f"capture_{timestamp}")
        os.makedirs(self.captureSequenceDir, exist_ok=True)

        # DB session created
        self.db_capture_session_id = start_capture_session(
            device_id=self.db_device_id,
            config_id=self.db_config_id,
            output_dir=out_dir,
            fps=float(fps),
            status="RUNNING"
        )
        log_event(self.db_capture_session_id, "CAPTURE_START", "INFO", f"out_dir={out_dir}, fps={fps}")

        self.contCaptureActive = True
        self.contCaptureFrameIdx = 0

        # open CSV
        csv_path = os.path.join(self.captureSequenceDir, f"frames_{timestamp}.csv")
        self.contCaptureCsvFile = open(csv_path, "w", newline="")
        self.contCaptureCsvWriter = csv.writer(self.contCaptureCsvFile)
        self.contCaptureCsvWriter.writerow(["frame_idx", "filename", "t_wall_sec", "t_mono_sec"])

        self.contCaptureStartWall = time.time()
        self.contCaptureStartMono = time.monotonic()

        interval_ms = int(max(1, round(1000.0 / float(fps))))
        self.contCaptureTimer.start(interval_ms)

        self.startContCaptureButton.setEnabled(False)
        self.stopContCaptureButton.setEnabled(True)
        self.log(f"[Continuous Capture] STARTED @ ~{fps} fps -> {out_dir}")


    def stopContinuousCapture(self):
        if not self.contCaptureActive:
            return

        self.contCaptureTimer.stop()
        self.contCaptureActive = False

        if self.contCaptureCsvFile is not None:
            try:
                self.contCaptureCsvFile.close()
            except Exception:
                pass
        self.contCaptureCsvFile = None
        self.contCaptureCsvWriter = None

        self.startContCaptureButton.setEnabled(True)
        self.stopContCaptureButton.setEnabled(False)
        self.log(f"[Continuous Capture] STOPPED. Saved {self.contCaptureFrameIdx} frames.")

        if self.db_capture_session_id is not None:
            log_event(self.db_capture_session_id, "CAPTURE_STOP", "INFO", "Stopped by user")
            end_capture_session(self.db_capture_session_id, status="COMPLETED")
            self.db_last_capture_dir = self.captureSequenceDir
            self.db_last_session_id = self.db_capture_session_id
            self.db_capture_session_id = None

        self.saveCaptureToDB.setEnabled(True)

    def saveCaptureToDatabase(self):
         # --- PLUS .mha path (from startCaptureSeq) ---
        if self.plusOutPath and os.path.isfile(self.plusOutPath):
            session_id = start_capture_session(
                device_id=self.db_device_id,
                config_id=self.db_config_id,
                output_dir=str(Path(self.plusOutPath).parent),
                fps=0.0,
                status="SAVED",
            )
            end_capture_session(session_id, status="SAVED")
            artifact_id = add_ultrasound_stream(
                session_id=session_id,
                file_path=self.plusOutPath,
                stream_type="MHA",
            )
            log_event(session_id, "MHA_SAVED", "INFO", f"artifact_id={artifact_id}, path={self.plusOutPath}")
            self.log(f"[DB] .mha registered → artifact_id={artifact_id}")
            QtWidgets.QMessageBox.information(
                self, "Saved to Database",
                f"Artifact ID: {artifact_id}\n{self.plusOutPath}"
            )

        # --- Continuous capture path (folder of .png frames) ---
        elif hasattr(self, "db_last_capture_dir") and self.db_last_capture_dir:
            session_id = self.db_last_session_id
            end_capture_session(session_id, status="SAVED")
            artifact_id = add_ultrasound_stream(
                session_id=session_id,
                file_path=self.db_last_capture_dir,
                stream_type="FRAMES_DIR",
            )
            log_event(session_id, "CAPTURE_SAVED", "INFO",
                      f"artifact_id={artifact_id}, path={self.db_last_capture_dir}")
            self.log(f"[DB] Capture folder registered → artifact_id={artifact_id}")
            QtWidgets.QMessageBox.information(
                self, "Saved to Database",
                f"Artifact ID: {artifact_id}\n{self.db_last_capture_dir}"
            )

        else:
            QtWidgets.QMessageBox.warning(
                self, "Nothing to Save",
                "No completed capture found.\nRun and stop a capture first."
            )
            return

        self.saveCaptureToDB.setEnabled(False)

    def loadDeviceConfig(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Device Config XML", QtCore.QDir.currentPath(), "XML Files (*.xml)"
        )
        if not fname:
            return

        self.db_config_id = create_device_config(
            device_id=self.db_device_id,
            config_path=fname,
            config_type="PLUS_DEVICESET",
            notes="User-uploaded device configuration"
        )

        self.log(f"Device config loaded: {fname}")
        log_event(None, "CONFIG_LOADED", "INFO", f"config_id={self.db_config_id}, path={fname}")


    def _contCaptureTick(self):
        if not self.contCaptureActive:
            return

        self.captureSequenceIdx = self.contCaptureFrameIdx + 1
        self.captureFrame()
