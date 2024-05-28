# import vtk
#
# # Define the custom right mouse button event handler
# def customRightButtonPressCallback(caller, event):
#     print("Right mouse button pressed.")
#     # Add your custom actions here
#
# def customRightButtonReleaseCallback(caller, event):
#     print("Right mouse button released.")
#     # Add your custom actions here
#
# # Function to add observers to a slice view interactor
# def addRightButtonObservers(interactor):
#     interactor.AddObserver(vtk.vtkCommand.RightButtonPressEvent, customRightButtonPressCallback)
#     interactor.AddObserver(vtk.vtkCommand.RightButtonReleaseEvent, customRightButtonReleaseCallback)
#
# # Get the layout manager
# layoutManager = slicer.app.layoutManager()
#
# # Iterate over all slice views
# for sliceViewName in layoutManager.sliceViewNames():
#     sliceWidget = layoutManager.sliceWidget(sliceViewName)
#     interactor = sliceWidget.sliceView().interactor()
#     addRightButtonObservers(interactor)
#
# # Also add observers to the 3D view
# threeDView = layoutManager.threeDWidget(0).threeDView()
# addRightButtonObservers(threeDView.interactor())

import vtk

# Define the custom right mouse button event handler
def customRightButtonPressCallback(caller, event):
    print("Right mouse button pressed.")
    # Add your custom actions here

def customRightButtonReleaseCallback(caller, event):
    print("Right mouse button released.")
    # Add your custom actions here

# Function to add observers to a slice view interactor
def addRightButtonObservers(interactor):
    interactor.AddObserver(vtk.vtkCommand.RightButtonPressEvent, customRightButtonPressCallback)
    interactor.AddObserver(vtk.vtkCommand.RightButtonReleaseEvent, customRightButtonReleaseCallback)

# Get the layout manager
layoutManager = slicer.app.layoutManager()

# Iterate over all slice views
for sliceViewName in layoutManager.sliceViewNames():
    sliceWidget = layoutManager.sliceWidget(sliceViewName)
    interactor = sliceWidget.sliceView().interactor()
    addRightButtonObservers(interactor)

# Also add observers to the 3D view
threeDView = layoutManager.threeDWidget(0).threeDView()
addRightButtonObservers(threeDView.interactor())

