'''
 Create a geometry node called "geo" and put the code in a python SOP
'''

import hou

# Get scene root node
sceneRoot = hou.node('/obj/')
geo = sceneRoot.node('geo')

# create node only when not existing
if geo.node('sphere_top') == None:
    sphere_top = geo.createNode('sphere', 'sphere_top')
sphere_top = geo.node('sphere_top')

if geo.node('sphere_bot') == None:
    sphere_bot = geo.createNode('sphere', 'sphere_bot')
sphere_bot = geo.node('sphere_bot')

if geo.node('tube') == None:
    tube = geo.createNode('tube', 'tube')
tube = geo.node('tube')

if geo.node('merge') == None:
    merge = geo.createNode('merge', 'merge')
merge = geo.node('merge')

# modify the shape
CNC_length = 10
CNC_width = 2

sphere_top.parm('ty').set(CNC_length/2)
sphere_bot.parm('ty').set(-CNC_length/2)
for i in ['radx', 'rady', 'radz']:
    sphere_top.parm(i).set(CNC_width/2)
    sphere_bot.parm(i).set(CNC_width/2)

tube.parm('height').set(CNC_length)
tube.parm('rad1').set(CNC_width/2)
tube.parm('rad2').set(CNC_width/2)

# join the parts to make CNC rods
for i, node in enumerate([sphere_top, sphere_bot, tube]):
    merge.setInput(i, node)


# create grid for anchoring
if geo.node('grid') == None:
    grid = geo.createNode('grid', 'grid')
grid = geo.node('grid')

# modify the grid
cols = 20
rows = cols / (CNC_length/CNC_width) + 1


grid.parm('sizex').set(cols*CNC_width*2)
grid.parm('sizey').set(rows*CNC_length * 1.5)
grid.parm('rows').set(rows)
grid.parm('cols').set(cols)


# create copytogrids
if geo.node('copytopoints') == None:
    copytopoints = geo.createNode('copytopoints', 'copytopoints')
copytopoints = geo.node('copytopoints')

copytopoints.setInput(0, merge)
copytopoints.setInput(1, grid)



if geo.node('attribwrangle') == None:
    attribwrangle = geo.createNode('attribwrangle', 'attribwrangle')
attribwrangle = geo.node('attribwrangle')


attribwrangle.setInput(0, grid)
copytopoints.setInput(1, attribwrangle)

attribwrangle.parm('snippet').set(
    '''
    v@P+=v@P*float(rand(@ptnum));
    p@orient[0]=1;
    ''')


if geo.node('python_wrangle') == None:
    python_wrangle = geo.createNode('python', 'python_wrangle')
python_wrangle = geo.node('python_wrangle')


python_wrangle.setInput(0, attribwrangle)
copytopoints.setInput(1, python_wrangle)

python_wrangle.parm('python').set(
'''
node = hou.pwd()
geo = node.geometry()
for point in geo.points():
    position = point.position()
    # print(position)
    point.setPosition((position[0], position[1], position[2]))
''')
