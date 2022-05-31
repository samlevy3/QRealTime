# Service Development Guide

## Relevant Folders and Files
- `Service` folder: holds `Service.py` and files for service classes
- `Service/Service.py`: has superclass `Service` for services that
   sets up service, provides helper methods, and defines required methods
- `helper` folder: holds any shared helper methods for services
- `helper/layer2form.py`: holds shared helper methods for converting a layer to a specific form format
- `QRealTime_dialog.py`: Sets up the UI for each service
-  `QRealTime.py`: QGIS plugin implementation that calls methods for the chosen service

## Steps to Create a New Service
1. Create a file in the `Service` folder holding a subclass of the `Service` class
(defined in `Service.py`). The `Service` class has a variet of helper methods that
can be used by every service.
2. Implement the functionality for the required methods (listed below). Any method that is not
implemented will throw a `NotImplementedError`.
3. Add service to list in `QRealTime_dialog.py`

*For examples of services and implementations of the required methods, see `Aggregate.py`, `Central.py`, or `Kobo.py`.*


## Description of Required Methods
### sendForm
- Takes in a layer and converts to a form
- Uses an HTTP request to publish the form in the online server
- Calls `self.getFormList(...)` to get a list of all forms
- Tip: can use `layer2XForm` method (defined in `later2form.py`) to convert a layer to an Xform
before sending it to the server

### importData
- Imports the selected form from the server
- Calls `self.collectData(...)` (defined in `Service.py`) to process the data and update the layer

### getTable
- Retrieves data from form table and filters it to only get the necessary fields
- Called by `self.collectData(...)` (defined in `Service.py`)

### getFormList
- Retrieves list of all forms by sedning a request to the server using the credentials entered by the user
- Called by `self.sendForm(...)`

### setParameters
- Lists user inputs for the UI for the service that will be accessed via `self.getValue(...)` (defined in `Service.py`)
- Called in `init` for the `Service` class
- EX: url and credientials to access the server