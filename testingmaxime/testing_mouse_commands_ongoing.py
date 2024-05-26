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
        center = [self.GetInteractor().GetSize()[0] / 2,
                  self.GetInteractor().GetSize()[1] / 2]

        if self.zooming:
            distance_to_center = ((currentPos[0] - center[0]) ** 2 + (
                        currentPos[1] - center[1]) ** 2) ** 0.5
            distance_to_last = ((self.lastPos[0] - center[0]) ** 2 + (
                        self.lastPos[1] - center[1]) ** 2) ** 0.5

            if distance_to_last != 0:
                factor = distance_to_center / distance_to_last
            else:
                factor = 1.0

            sliceNode = self.sliceLogic.GetSliceNode()
            fov = sliceNode.GetFieldOfView()

            # Limiting zoom speed to avoid too fast zooming
            max_zoom_factor = 1.5
            min_zoom_factor = 0.5
            factor = max(min(factor, max_zoom_factor), min_zoom_factor)

            sliceNode.SetFieldOfView(fov[0] * factor, fov[1] * factor, fov[2])
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
