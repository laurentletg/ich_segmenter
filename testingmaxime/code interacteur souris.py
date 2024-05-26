# ###fait en sorte que print mouse moved quand la souris bouge
import vtk
import slicer

class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self):
        vtk.vtkInteractorStyleImage.__init__(self)
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
        self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonReleaseEvent)
        self.startPosition = None
        self.panning = False

    def onLeftButtonPressEvent(self, obj, event):
        print("Left button pressed")
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.panning = True
        self.OnLeftButtonDown()
        return

    def onMouseMoveEvent(self, obj, event):
        print("Mouse moved")
        if self.panning and self.startPosition:
            currentPosition = self.GetInteractor().GetEventPosition()
            deltaX = self.startPosition[0] - currentPosition[0]
            deltaY = self.startPosition[1] - currentPosition[1]

            # Adjust the camera position based on mouse movement
            renderer = self.GetInteractor().FindPokedRenderer(currentPosition[0], currentPosition[1])
            if renderer:
                camera = renderer.GetActiveCamera()
                focalPoint = camera.GetFocalPoint()
                position = camera.GetPosition()
                viewUp = camera.GetViewUp()
                right = [0, 0, 0]
                vtk.vtkMath.Cross(viewUp, focalPoint, right)
                camera.SetFocalPoint(focalPoint[0] + right[0]*deltaX + viewUp[0]*deltaY,
                                     focalPoint[1] + right[1]*deltaX + viewUp[1]*deltaY,
                                     focalPoint[2] + right[2]*deltaX + viewUp[2]*deltaY)
                camera.SetPosition(position[0] + right[0]*deltaX + viewUp[0]*deltaY,
                                   position[1] + right[1]*deltaX + viewUp[1]*deltaY,
                                   position[2] + right[2]*deltaX + viewUp[2]*deltaY)
                renderer.ResetCameraClippingRange()
                self.GetInteractor().Render()

            self.startPosition = currentPosition
        else:
            # Call default mouse interaction when panning is not active
            self.OnMouseMove()
        return

    def onLeftButtonReleaseEvent(self, obj, event):
        print("Left button released")
        self.startPosition = None
        self.panning = False
        self.OnLeftButtonUp()
        return

# Get the interactor from the 'Yellow' slice view
interactor = slicer.app.layoutManager().sliceWidget('Yellow').sliceView().interactor()

# Apply the custom interactor style
style = CustomInteractorStyle()
interactor.SetInteractorStyle(style)
