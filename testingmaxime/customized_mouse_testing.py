#
#
# ###fonctionne pour maintien de la souris et naviguer au travers des images
# #mais toutes les autres fonctions de base sont perdues
# import vtk
# import slicer
#
#
# class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
#     def __init__(self, parent=None):
#         self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
#         self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
#         self.AddObserver("LeftButtonReleaseEvent",
#                          self.onLeftButtonReleaseEvent)
#         self.startPosition = None
#         self.sliceLogic = slicer.app.layoutManager().sliceWidget(
#             'Yellow').sliceLogic()
#         self.sliceNode = self.sliceLogic.GetSliceNode()
#
#     def onLeftButtonPressEvent(self, obj, event):
#         self.startPosition = self.GetInteractor().GetEventPosition()
#         self.OnLeftButtonDown()
#         return
#
#     def onMouseMoveEvent(self, obj, event):
#         if self.startPosition:
#             currentPosition = self.GetInteractor().GetEventPosition()
#             deltaX = currentPosition[0] - self.startPosition[0]
#             deltaY = currentPosition[1] - self.startPosition[1]
#
#             fov = self.sliceNode.GetFieldOfView()
#             aspectRatio = fov[0] / fov[1]
#             deltaOffsetX = -deltaX * fov[0] / \
#                            self.sliceLogic.GetSliceNode().GetDimensions()[0]
#             deltaOffsetY = deltaY * fov[1] / \
#                            self.sliceLogic.GetSliceNode().GetDimensions()[1]
#
#             self.sliceNode.SetSliceOffset(
#                 self.sliceNode.GetSliceOffset() + deltaOffsetY)
#             self.sliceNode.Modified()
#
#             self.startPosition = currentPosition
#         self.OnMouseMove()
#         return
#
#     def onLeftButtonReleaseEvent(self, obj, event):
#         self.startPosition = None
#         self.OnLeftButtonUp()
#         return
#
#
# # Get the interactor from the 'Yellow' slice view
# interactor = slicer.app.layoutManager().sliceWidget(
#     'Yellow').sliceView().interactor()
#
# # Apply the custom interactor style
# style = CustomInteractorStyle()
# interactor.SetInteractorStyle(style)




#################
#permet de naviguer images
# import vtk
# import slicer
#
# class PanImageInteractorStyle(vtk.vtkInteractorStyleImage):
#     def __init__(self):
#         self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
#         self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
#         self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonReleaseEvent)
#         self.startPosition = None
#         self.sliceLogic = slicer.app.layoutManager().sliceWidget('Yellow').sliceLogic()
#         self.sliceNode = self.sliceLogic.GetSliceNode()
#         self.panning = False
#
#     def onLeftButtonPressEvent(self, obj, event):
#         self.startPosition = self.GetInteractor().GetEventPosition()
#         self.panning = True
#         self.OnLeftButtonDown()
#         return
#
#     def onMouseMoveEvent(self, obj, event):
#         if self.panning and self.startPosition:
#             currentPosition = self.GetInteractor().GetEventPosition()
#             deltaX = currentPosition[0] - self.startPosition[0]
#             deltaY = currentPosition[1] - self.startPosition[1]
#
#             # Adjust the pan based on the mouse movement
#             fov = self.sliceNode.GetFieldOfView()
#             aspectRatio = fov[0] / fov[1]
#             deltaOffsetX = -deltaX * fov[0] / self.sliceNode.GetDimensions()[0]
#             deltaOffsetY = deltaY * fov[1] / self.sliceNode.GetDimensions()[1]
#
#             sliceOffset = self.sliceNode.GetSliceOffset()
#             self.sliceNode.SetSliceOffset(sliceOffset + deltaOffsetY)
#             self.sliceNode.Modified()
#
#             # Pan the slice view
#             pan = self.sliceNode.GetXYZOrigin()
#             self.sliceNode.SetXYZOrigin(pan[0] + deltaOffsetX, pan[1], pan[2])
#             self.sliceNode.Modified()
#
#             self.startPosition = currentPosition
#         self.OnMouseMove()
#         return
#
#     def onLeftButtonReleaseEvent(self, obj, event):
#         self.startPosition = None
#         self.panning = False
#         self.OnLeftButtonUp()
#         return
#
# # Get the interactor from the 'Yellow' slice view
# yellowWidget = slicer.app.layoutManager().sliceWidget('Yellow')
# interactor = yellowWidget.sliceView().interactor()
#
# # Apply the custom interactor style
# style = PanImageInteractorStyle()
# interactor.SetInteractorStyle(style)


###script working from unintuitive direction and too fast
# import vtk
# import slicer
#
# class PanImageInteractorStyle(vtk.vtkInteractorStyleImage):
#     def __init__(self):
#         self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
#         self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
#         self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonReleaseEvent)
#         self.startPosition = None
#         self.sliceWidget = slicer.app.layoutManager().sliceWidget('Yellow')
#         self.sliceNode = self.sliceWidget.mrmlSliceNode()
#         self.panning = False
#
#     def onLeftButtonPressEvent(self, obj, event):
#         self.startPosition = self.GetInteractor().GetEventPosition()
#         self.panning = True
#         self.OnLeftButtonDown()
#         return
#
#     def onMouseMoveEvent(self, obj, event):
#         if self.panning and self.startPosition:
#             currentPosition = self.GetInteractor().GetEventPosition()
#             deltaX = currentPosition[0] - self.startPosition[0]
#             deltaY = currentPosition[1] - self.startPosition[1]
#
#             # Adjust the image position based on mouse movement
#             pan = self.sliceNode.GetXYZOrigin()
#             self.sliceNode.SetXYZOrigin(pan[0] - deltaX, pan[1] + deltaY, pan[2])
#             self.sliceNode.Modified()
#
#             self.startPosition = currentPosition
#         self.OnMouseMove()
#         return
#
#     def onLeftButtonReleaseEvent(self, obj, event):
#         self.startPosition = None
#         self.panning = False
#         self.OnLeftButtonUp()
#         return
#
# # Get the interactor from the 'Yellow' slice view
# interactor = slicer.app.layoutManager().sliceWidget('Yellow').sliceView().interactor()
#
# # Apply the custom interactor style
# style = PanImageInteractorStyle()
# interactor.SetInteractorStyle(style)


##### script working left button moving image
# import vtk
# import slicer
#
# class PanImageInteractorStyle(vtk.vtkInteractorStyleImage):
#     def __init__(self):
#         self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPressEvent)
#         self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
#         self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonReleaseEvent)
#         self.startPosition = None
#         self.sliceWidget = slicer.app.layoutManager().sliceWidget('Yellow')
#         self.sliceNode = self.sliceWidget.mrmlSliceNode()
#         self.panning = False
#
#     def onLeftButtonPressEvent(self, obj, event):
#         self.startPosition = self.GetInteractor().GetEventPosition()
#         self.panning = True
#         self.OnLeftButtonDown()
#         return
#
#     def onMouseMoveEvent(self, obj, event):
#         if self.panning and self.startPosition:
#             currentPosition = self.GetInteractor().GetEventPosition()
#             deltaX = self.startPosition[0] - currentPosition[0]
#             deltaY = self.startPosition[1] - currentPosition[1]
#
#             # Adjust the image position based on mouse movement
#             pan = self.sliceNode.GetXYZOrigin()
#             self.sliceNode.SetXYZOrigin(pan[0] + deltaX, pan[1] + deltaY, pan[2])
#             self.sliceNode.Modified()
#
#             self.startPosition = currentPosition
#         self.OnMouseMove()
#         return
#
#     def onLeftButtonReleaseEvent(self, obj, event):
#         self.startPosition = None
#         self.panning = False
#         self.OnLeftButtonUp()
#         return
#
# # Get the interactor from the 'Yellow' slice view
# interactor = slicer.app.layoutManager().sliceWidget('Yellow').sliceView().interactor()
#
# # Apply the custom interactor style
# style = PanImageInteractorStyle()
# interactor.SetInteractorStyle(style)

##code working with right button
import vtk
import slicer

class PanImageInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self):
        self.AddObserver("RightButtonPressEvent", self.onRightButtonPressEvent)
        self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonReleaseEvent)
        self.startPosition = None
        self.sliceWidget = slicer.app.layoutManager().sliceWidget('Yellow')
        self.sliceNode = self.sliceWidget.mrmlSliceNode()
        self.panning = False

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
        self.OnMouseMove()
        return

    def onRightButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.panning = False
        self.OnRightButtonUp()
        return

# Get the interactor from the 'Yellow' slice view
interactor = slicer.app.layoutManager().sliceWidget('Yellow').sliceView().interactor()

# Apply the custom interactor style
style = PanImageInteractorStyle()
interactor.SetInteractorStyle(style)



