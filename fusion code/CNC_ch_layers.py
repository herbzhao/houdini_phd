# Author-
# Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
import math
import random


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        # create a new file
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        yzPlane = rootComp.yZConstructionPlane
        xzPlane = rootComp.xZConstructionPlane
        xAxis = rootComp.xConstructionAxis
        yAxis = rootComp.yConstructionAxis
        zAxis = rootComp.zConstructionAxis

        def create_CNC(center=(0, 0, 0), length=10, width=5, name="CNC"):
            sketch = sketches.add(xyPlane)

            # Draw a circle.
            ellipses = sketch.sketchCurves.sketchEllipses
            CNC_profile = ellipses.add(
                adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(0, length / 2, 0), adsk.core.Point3D.create(width / 2, 0, 0)
            )

            # Draw a line to use as the axis of revolution.
            lines = sketch.sketchCurves.sketchLines
            circle_axisLine = lines.addByTwoPoints(
                adsk.core.Point3D.create(center[0], center[1] - length / 2, center[2]),
                adsk.core.Point3D.create(center[0], center[1] + length / 2, center[2]),
            )

            # Get the profile defined by the circle.
            circle_prof = sketch.profiles.item(0)

            # Create an revolution input to be able to define the input needed for a revolution
            # while specifying the profile and that a new component is to be created
            revolves = rootComp.features.revolveFeatures
            revolves_input = revolves.createInput(circle_prof, circle_axisLine, adsk.fusion.FeatureOperations.NewComponentFeatureOperation)

            # Define that the extent is an angle of pi to get half of a torus.
            angle = adsk.core.ValueInput.createByReal(360 / 360 * 2 * math.pi)
            revolves_input.setAngleExtent(False, angle)

            # Create the extrusion.
            ext = revolves.add(revolves_input)
            # a component that allows further manipulation
            comp = ext.parentComponent
            comp.name = name
            body = comp.bRepBodies.item(0)
            body.name = name
            return comp

        def change_appearance(body, rgb=(0, 0, 0), base_appearance_name="Plastic - Translucent Glossy (Yellow)", new_appearance_name="new_color"):
            # https://ekinssolutions.com/setting-colors-in-fusion-360/
            # Get the single occurrence that references the component.

            # Get a reference to an appearance in the library.
            materials_library = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
            base_appearance = materials_library.appearances.itemByName(base_appearance_name)

            # Create a copy of the existing appearance for the glossy etc.
            new_appearance = design.appearances.addByCopy(base_appearance, str(new_appearance_name))

            # Edit the "Color" property by setting it to a random color.
            color_property = adsk.core.ColorProperty.cast(new_appearance.appearanceProperties.itemByName("Color"))
            color_property.value = adsk.core.Color.create(*rgb, 1)

            # Assign the new color to the occurrence.
            body.appearance = new_appearance

        def print_ui(message):
            ui.messageBox("{}".format(message))

        def circular_pattern(body):
            # Get the body created by extrusion

            # Create input entities for circular pattern
            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(body)

            # Get Y axis for circular pattern

            # Create the input for circular pattern
            circularFeats = rootComp.features.circularPatternFeatures
            circularFeatInput = circularFeats.createInput(inputEntites, zAxis)

            # Set the quantity of the elements
            circularFeatInput.quantity = adsk.core.ValueInput.createByReal(5)

            # Set the angle of the circular pattern
            circularFeatInput.totalAngle = adsk.core.ValueInput.createByString("180 deg")

            # Set symmetry of the circular pattern
            circularFeatInput.isSymmetric = False

            # Create the circular pattern
            circularFeat = circularFeats.add(circularFeatInput)

        def rectangular_pattern(body, component, axis1=xAxis, axis2=yAxis, quantity1=10, quantity2=10, distance1=200, distance2=200):
            # Create input entities for circular pattern
            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(body)

            # Quantity and distance
            quantity1 = adsk.core.ValueInput.createByReal(quantity1)
            distance1 = adsk.core.ValueInput.createByReal(distance1)
            quantity2 = adsk.core.ValueInput.createByReal(quantity2)
            distance2 = adsk.core.ValueInput.createByReal(distance2)

            # Create the input for rectangular pattern
            rectangularPatterns = component.features.rectangularPatternFeatures
            rectangularPatternInput = rectangularPatterns.createInput(
                inputEntites, axis1, quantity1, distance1, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
            )
            rectangularPatternInput.isSymmetricInDirectionOne = True

            # Set the data for second direction
            rectangularPatternInput.setDirectionTwo(axis2, quantity2, distance2)

            rectangularPatternInput.isSymmetricInDirectionTwo = True

            # Create the rectangular pattern
            rectangularFeature = rectangularPatterns.add(rectangularPatternInput)

        def move_body(body, component, distance=(20, 0, 0), rotation=(90, 0, 0), copy=True):
            """
            specify which body and which component it belongs to
            """
            # https://adndevblog.typepad.com/manufacturing/2017/08/fusion-360-api-transform-component-.html
            # choose the occurance (instance of the comp)
            # Create a transform to do move
            transform = adsk.core.Matrix3D.create()

            # translation
            vector = adsk.core.Vector3D.create(*distance)
            transform.translation = vector

            # transformation matrices but they're commonly used in computer graphics.
            # Using matrix functionality you can build up a matrix using multiple rotations and then use that to create a Move feature.
            axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
            for angle, axis in zip(rotation, axes):
                rotation = adsk.core.Matrix3D.create()
                rotation.setToRotation(angle / 360 * 2 * math.pi, adsk.core.Vector3D.create(*axis), adsk.core.Point3D.create(0, 0, 0))
                transform.transformBy(rotation)

            # Create a move feature
            moveFeats = component.features.moveFeatures

            inputEntites = adsk.core.ObjectCollection.create()
            inputEntites.add(body)

            moveFeatureInput = moveFeats.createInput(inputEntites, transform)
            moveFeats.add(moveFeatureInput)

            # capture the position
            # https://forums.autodesk.com/t5/fusion-360-api-and-scripts/transformation-on-occurrence-getting-reset/td-p/8394257
            # if distance != (0,0,0) or rotation !=(0,0,0):
            try:
                design.snapshots.add()
            except RuntimeError:
                pass

        def move_comp(comp, distance=(20, 0, 0), rotation = (90, 0, 0), copy = True):
            # https://adndevblog.typepad.com/manufacturing/2017/08/fusion-360-api-transform-component-.html
            # choose the occurance (instance of the comp) 
            # https://adndevblog.typepad.com/manufacturing/2017/08/fusion-360-api-transform-component-.html
            # choose the occurance (instance of the comp)
            # Create a transform to do move
            transform = adsk.core.Matrix3D.create()


            bodies = adsk.core.ObjectCollection.create()
            for i in range(comp.bRepBodies.count):
                bodies.add(comp.bRepBodies.item(i))

            # translation
            vector = adsk.core.Vector3D.create(*distance)
            transform.translation = vector

            # transformation matrices but they're commonly used in computer graphics.
            # Using matrix functionality you can build up a matrix using multiple rotations and then use that to create a Move feature.
            axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
            for angle, axis in zip(rotation, axes):
                rotation = adsk.core.Matrix3D.create()
                rotation.setToRotation(angle / 360 * 2 * math.pi, adsk.core.Vector3D.create(*axis), adsk.core.Point3D.create(0, 0, 0))
                transform.transformBy(rotation)

            # Create a move feature
            moveFeats = comp.features.moveFeatures

            moveFeatureInput = moveFeats.createInput(bodies, transform)
            moveFeats.add(moveFeatureInput)

            # capture the position
            # https://forums.autodesk.com/t5/fusion-360-api-and-scripts/transformation-on-occurrence-getting-reset/td-p/8394257
            # if distance != (0,0,0) or rotation !=(0,0,0):
            try:
                design.snapshots.add()
            except RuntimeError:
                pass


        def copy_component(comp, new_comp="", name="item"):
            # comp_copy = rootComp.occurrences.addByInsert(comp, adsk.core.Matrix3D.create(), False)
            #  create an empty comp
            # new_comp = adsk.core.ObjectCollection.create()
            if new_comp == "":
                new_comp = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                new_comp.component.name = name + "_copy"
                new_comp = new_comp.component

            # https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-1dad75dc-4bf8-11e7-bf09-005056c00008
            # Get the first body in sub component 1
            bodies = []
            for i in range(comp.bRepBodies.count):
                bodies.append(comp.bRepBodies.item(i))

            # Copy/paste body from sub component 1 to sub component 2
            for body in bodies:
                copyPasteBody = new_comp.features.copyPasteBodies.add(body)

            return new_comp

        def select_all_bodies(component):
            bodies = []
            for i in range(component.bRepBodies.count):
                bodies.append(component.bRepBodies.item(i))

            return bodies

        def create_cholesteric(CNC_length, CNC_width, half_pitch, lines, rows, slices, repeats=1):
            """
            lins, rows, and slices -- x, y, z repeats
            """
            original_CNC_comp = create_CNC(length=CNC_length, width=CNC_width, name="CNC")
            for r in range(repeats):
                CNC_comp_set = []
                for s in range(slices):
                    # ignore the second repeat's first layer
                    if r != 0 and s ==0:
                        CNC_comp_set.append('Empty')

                    else:
                        CNC_comp_set.append(copy_component(original_CNC_comp))
                        # select the body and move up for stacking
                        body = select_all_bodies(CNC_comp_set[s])[0]

                        rectangular_pattern(
                            body,
                            CNC_comp_set[s],
                            axis1=xAxis,
                            axis2=yAxis, 
                            quantity1=lines,
                            quantity2=rows,
                            distance1=CNC_width * 3,
                            distance2=CNC_length * 1,
                        )
                        
                        all_body = select_all_bodies(CNC_comp_set[s])
                        for body in all_body:
                            # create some jiggering
                            change_appearance(body, rgb=(0, 255, 0))
                            move_body(
                                body,
                                CNC_comp_set[s],
                                distance=(
                                    random.uniform(-CNC_width / 10, CNC_width / 10),
                                    random.uniform(-CNC_length / 20, CNC_length / 20),
                                    random.uniform(-CNC_width / 10, CNC_width / 10),
                                ),
                                rotation=(random.uniform(-2, 2), 0, random.uniform(-5, 5)),
                                copy=False,
                            )
                    
                        #  rotate the layer
                        if s>=1:
                            move_comp(CNC_comp_set[s], distance=(0, 0, s * half_pitch / (slices-1) + r * half_pitch), rotation=(0, 0, int(180/(slices-1)*s)))


        # NOTE: actual code runs here
        CNC_length = 40
        CNC_width = 2
        # lines = 20
        # rows = 3
        lines = 20
        rows = 3
        half_pitch = CNC_width * 40

        create_cholesteric(
            CNC_length, CNC_width, half_pitch, lines,  rows, slices=10, repeats = 1
        )

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

