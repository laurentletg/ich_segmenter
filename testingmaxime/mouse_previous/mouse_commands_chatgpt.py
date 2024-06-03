import vtk
import slicer


class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, sliceLogic):
        self.sliceLogic = sliceLogic
        self.zooming = False
        self.panning = False
        self.AddObserver("RightButtonPressEvent", self.start_zoom)
        self.AddObserver("RightButtonReleaseEvent", self.stop_zoom)
        self.AddObserver("LeftButtonPressEvent", self.toggle_pan)
        self.AddObserver("MouseMoveEvent", self.pan_or_zoom_move)
        self.lastPos = None

    def start_zoom(self, obj, event):
        self.zooming = True
        self.lastPos = self.GetInteractor().GetEventPosition()
        self.OnRightButtonDown()
        return

    def stop_zoom(self, obj, event):
        self.zooming = False
        self.OnRightButtonUp()
        return

    def toggle_pan(self, obj, event):
        self.panning = not self.panning
        if self.panning:
            self.lastPos = self.GetInteractor().GetEventPosition()
        self.OnLeftButtonDown()
        return

    def pan_or_zoom_move(self, obj, event):
        currentPos = self.GetInteractor().GetEventPosition()
        if self.zooming:
            deltaY = currentPos[1] - self.lastPos[1]
            factor = 1.01 if deltaY > 0 else 0.99

            sliceNode = self.sliceLogic.GetSliceNode()
            fov = sliceNode.GetFieldOfView()
            sliceNode.SetFieldOfView(fov[0] * factor, fov[1] * factor, fov[2])
            self.sliceLogic.FitSliceToBackground()
        elif self.panning:
            deltaX = currentPos[0] - self.lastPos[0]
            deltaY = currentPos[1] - self.lastPos[1]

            sliceNode = self.sliceLogic.GetSliceNode()
            offsetX = deltaX * sliceNode.GetFieldOfView()[0] / 1000
            offsetY = deltaY * sliceNode.GetFieldOfView()[1] / 1000

            sliceNode.SetSliceOffset(sliceNode.GetSliceOffset() - offsetY)

        self.lastPos = currentPos
        self.OnMouseMove()
        return


# Get the layout manager and slice logic for the desired slice view
layoutManager = slicer.app.layoutManager()
yellowSliceWidget = layoutManager.sliceWidget('Yellow')
yellowSliceLogic = yellowSliceWidget.sliceLogic()

# Set the custom interactor style
interactor = yellowSliceWidget.sliceView().interactorStyle().GetInteractor()
customInteractorStyle = CustomInteractorStyle(yellowSliceLogic)
interactor.SetInteractorStyle(customInteractorStyle)
