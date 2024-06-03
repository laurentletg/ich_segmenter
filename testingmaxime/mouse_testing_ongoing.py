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
        self.startPosition = None
        self.sliceWidget = slicer.app.layoutManager().sliceWidget('Yellow')
        self.sliceNode = self.sliceWidget.mrmlSliceNode()
        self.sliceLogic = slicer.app.applicationLogic().GetSliceLogic(self.sliceNode)
        self.panning = False
        self.zooming = False

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
            self.sliceNode.SetXYZOrigin(pan[0] + deltaX, pan[1] + deltaY, pan[2])
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

    def onMouseWheelForwardEvent(self, obj, event):
        # Move to the next slice
        currentOffset = self.sliceLogic.GetSliceOffset()
        newOffset = currentOffset + self.getSliceSpacing()  # Move one slice forward
        self.sliceLogic.SetSliceOffset(newOffset)
        self.OnMouseWheelForward()
        return

    def onMouseWheelBackwardEvent(self, obj, event):
        # Move to the previous slice
        currentOffset = self.sliceLogic.GetSliceOffset()
        newOffset = currentOffset - self.getSliceSpacing()  # Move one slice backward
        self.sliceLogic.SetSliceOffset(newOffset)
        self.OnMouseWheelBackward()
        return

    def zoom(self):
        sliceNode = self.sliceLogic.GetSliceNode()
        currentPos = self.GetInteractor().GetEventPosition()
        fov = sliceNode.GetFieldOfView()

        # Get the distance of the mouse cursor from the image center
        imageCenter = [fov[i] / 2 for i in range(3)]
        deltaX = currentPos[0] - imageCenter[0]
        deltaY = currentPos[1] - imageCenter[1]

        zoomFactor = 1.05 if deltaY > 0 else 0.95  # Adjust zoom factor as needed
        zoomSpeed = 1  # Adjust zoom speed as needed

        # Calculate new field of view
        newFovX = fov[0] * zoomFactor
        newFovY = fov[1] * zoomFactor
        newFovZ = fov[2]

        # Calculate the zoom center
        zoomCenterX = imageCenter[0] + deltaX
        zoomCenterY = imageCenter[1] + deltaY

        # Calculate the new image position
        newOriginX = zoomCenterX - newFovX / 2
        newOriginY = zoomCenterY - newFovY / 2

        # Update the slice node's field of view and position
        sliceNode.SetFieldOfView(newFovX, newFovY, newFovZ)
        sliceNode.SetXYZOrigin(newOriginX, newOriginY,
                               sliceNode.GetXYZOrigin()[2])

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
