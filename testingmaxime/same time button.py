#working great!!! The only default is that it does not zoom in the right
# directionzzzz
import vtk
import slicer

class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self):
        self.AddObserver("RightButtonPressEvent", self.onRightButtonPressEvent)
        self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonReleaseEvent)
        self.AddObserver("MouseWheelForwardEvent", self.onMouseWheelForwardEvent)
        self.AddObserver("MouseWheelBackwardEvent", self.onMouseWheelBackwardEvent)
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonReleaseEvent)
        self.AddObserver("KeyPressEvent", self.onKeyPressEvent) # Add KeyPressEvent observer
        #added by mb
        self.AddObserver("KeyReleaseEvent", self.onKeyReleaseEvent)# Add KeyPressEvent observer
        self.startPosition = None
        self.sliceWidget = slicer.app.layoutManager().sliceWidget('Yellow')
        self.sliceNode = self.sliceWidget.mrmlSliceNode()
        self.sliceLogic = slicer.app.applicationLogic().GetSliceLogic(self.sliceNode)
        self.panning = False
        self.zooming = False
        self.z_pressed = False

    def onRightButtonPressEvent(self, obj, event):
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.panning = True
        self.OnRightButtonDown()
        return

    def onMouseMoveEvent(self, obj, event):
        if self.panning and self.startPosition:
            currentPosition = self.GetInteractor().GetEventPosition()
            deltaX = self.startPosition[0] - currentPosition[0]
            deltaY = self.startPosition[1] - currentPosition[1]

            # Adjust the image position based on mouse movement
            pan = self.sliceNode.GetXYZOrigin()
            self.sliceNode.SetXYZOrigin(pan[0] + deltaX, pan[1] + deltaY,
                                        pan[2])
            self.sliceNode.Modified()

            self.startPosition = currentPosition
        elif self.zooming and self.startPosition:
            self.zoom()
            self.startPosition = self.GetInteractor().GetEventPosition()

        self.OnMouseMove()
        return

    def onRightButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.panning = False
        self.OnRightButtonUp()
        return

    def onLeftButtonPressEvent(self, obj, event):
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.zooming = True
        self.OnLeftButtonDown()
        return

    def onLeftButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.zooming = False
        self.OnLeftButtonUp()
        return
    def onKeyPressEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "z":
            self.z_pressed = True
            print("Z key pressed")
        self.OnKeyPress()
        return

    def onKeyReleaseEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "z":
            self.z_pressed = False
            print("Z key released")
        self.OnKeyRelease()
        return

    def onMouseWheelForwardEvent(self, obj, event):
        if self.z_pressed:
            print("Mouse scroll")
            # self.zooming = True
            self.zoom_in()
            print("self zoom done")
        else :
            # Move to the next slice
            currentOffset = self.sliceLogic.GetSliceOffset()
            newOffset = currentOffset + self.getSliceSpacing()  # Move one slice forward
            self.sliceLogic.SetSliceOffset(newOffset)
            self.OnMouseWheelForward()
        return

    def zoom_in(self):
        current_zoom = self.zoomFactor
        new_zoom = current_zoom * 1.1  # Zoom in by 10%
        self.setZoomFactor(new_zoom)

    def onMouseWheelBackwardEvent(self, obj, event):
        if self.z_pressed:
            print("Mouse scroll")

        # Move to the previous slice
        currentOffset = self.sliceLogic.GetSliceOffset()
        newOffset = currentOffset - self.getSliceSpacing()  # Move one slice backward
        self.sliceLogic.SetSliceOffset(newOffset)
        self.OnMouseWheelBackward()
        return

    def zoom(self):
        if self.startPosition:
            sliceNode = self.sliceLogic.GetSliceNode()
            fov = sliceNode.GetFieldOfView()
            currentPos = self.GetInteractor().GetEventPosition()
            deltaX = self.startPosition[0] - currentPos[0]
            deltaY = self.startPosition[1] - currentPos[1]

            factor = 1.01 if deltaY > 0 else 0.99
            zoomSpeed = 10  # Increase the zoom speed
            factor = factor ** (
                        abs(deltaY) / zoomSpeed)  # Adjust factor based on deltaY
            sliceNode.SetFieldOfView(fov[0] * factor, fov[1] * factor, fov[2])

    def getSliceSpacing(self):
        volumeNode = self.sliceLogic.GetBackgroundLayer().GetVolumeNode()
        if volumeNode:
            spacing = volumeNode.GetSpacing()
            return spacing[2]  # Return the spacing along the Z-axis
        return 1.0  # Default spacing if volumeNode is not available

# Get the interactor from the 'Yellow' slice view
interactor = slicer.app.layoutManager().sliceWidget('Yellow').sliceView().interactor()

# Apply the custom interactor style
style = CustomInteractorStyle()
interactor.SetInteractorStyle(style)
