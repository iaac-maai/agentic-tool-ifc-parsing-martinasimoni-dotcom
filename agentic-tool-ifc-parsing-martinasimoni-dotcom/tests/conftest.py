"""
Pytest fixtures for IFC compliance checker tests.
Provides sample IFC models for testing student implementations.
"""

import pytest
import ifcopenshell
import ifcopenshell.api
import tempfile
import os


@pytest.fixture
def simple_ifc_model():
    """
    Creates a simple IFC model with basic building elements for testing.
    
    Contains:
    - 1 IfcProject
    - 1 IfcSite
    - 1 IfcBuilding
    - 2 IfcBuildingStorey (Ground Floor, First Floor)
    - 3 IfcWall
    - 2 IfcDoor
    - 2 IfcWindow
    - 1 IfcSpace (Room)
    """
    model = ifcopenshell.file(schema="IFC4")
    
    # Create basic project structure using ifcopenshell.api
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="Test Project")
    
    # Create context
    context = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    
    # Create site
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Test Site")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])
    
    # Create building
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Test Building")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])
    
    # Create storeys
    ground_floor = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Ground Floor")
    ground_floor.Elevation = 0.0
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[ground_floor])
    
    first_floor = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="First Floor")
    first_floor.Elevation = 3000.0
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[first_floor])
    
    # Create walls
    for i in range(3):
        wall = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name=f"Wall {i+1}")
        ifcopenshell.api.run("spatial.assign_container", model, relating_structure=ground_floor, products=[wall])
    
    # Create doors
    for i in range(2):
        door = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcDoor", name=f"Door {i+1}")
        ifcopenshell.api.run("spatial.assign_container", model, relating_structure=ground_floor, products=[door])
    
    # Create windows
    for i in range(2):
        window = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWindow", name=f"Window {i+1}")
        ifcopenshell.api.run("spatial.assign_container", model, relating_structure=ground_floor, products=[window])
    
    # Create a space/room (IfcSpace is spatial, use aggregate not container)
    space = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSpace", name="Office Room")
    space.LongName = "Main Office Room 101"
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=ground_floor, products=[space])
    
    return model


@pytest.fixture
def empty_ifc_model():
    """Creates an empty IFC model with only a project."""
    model = ifcopenshell.file(schema="IFC4")
    ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="Empty Project")
    return model


@pytest.fixture
def ifc_model_with_properties(simple_ifc_model):
    """
    Extends simple_ifc_model with property sets for more advanced testing.
    
    Adds:
    - Fire rating properties to walls
    - Thermal properties to windows
    - Accessibility properties to doors
    """
    model = simple_ifc_model
    
    # Add properties to walls
    walls = model.by_type("IfcWall")
    for i, wall in enumerate(walls):
        pset = ifcopenshell.api.run("pset.add_pset", model, product=wall, name="Pset_WallCommon")
        ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties={
            "FireRating": f"REI{60 + i*30}",
            "IsExternal": i == 0,
            "LoadBearing": True,
        })
    
    # Add properties to doors
    doors = model.by_type("IfcDoor")
    for i, door in enumerate(doors):
        pset = ifcopenshell.api.run("pset.add_pset", model, product=door, name="Pset_DoorCommon")
        width = 900 if i == 0 else 800  # First door is accessible width
        ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties={
            "FireRating": "EI30",
            "IsExternal": i == 0,
        })
        # Set door dimensions
        door.OverallWidth = width
        door.OverallHeight = 2100
    
    # Add properties to windows
    windows = model.by_type("IfcWindow")
    for i, window in enumerate(windows):
        pset = ifcopenshell.api.run("pset.add_pset", model, product=window, name="Pset_WindowCommon")
        ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties={
            "ThermalTransmittance": 1.2 + i * 0.3,  # U-value
            "IsExternal": True,
        })
    
    return model


@pytest.fixture
def ifc_file_path(simple_ifc_model):
    """
    Saves simple_ifc_model to a temporary file and returns the path.
    Useful for testing file-based operations.
    """
    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as f:
        simple_ifc_model.write(f.name)
        yield f.name
    # Cleanup after test
    os.unlink(f.name)
