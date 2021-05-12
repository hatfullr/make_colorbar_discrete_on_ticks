def make_colorbar_discrete_on_ticks(colorbar,objects=None):
    # colorbar = the colorbar to change
    # objects = the plotted objects which will be affected by the colorbar change
    # Cover up the existing colorbar with a PatchCollection of Rectangles and
    # Polygons that span the colorbar and have the correct colors based on the
    # existing axis ticks. As such, make sure to call this method only AFTER
    # you are completely done setting up your colorbar (setting limits, sizing,
    # etc.)
    #
    # Your imshow data WILL BE MODIFIED in this method, so do not rely on it afterwards
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Polygon, Rectangle
    import numpy as np
    
    cmap = colorbar.get_cmap()
    clim = colorbar.get_clim()
    cax = colorbar.ax
    extend = colorbar.extend
    orientation = colorbar.orientation
    fig = cax.get_figure()
    figsize = fig.get_size_inches()
    
    extendfrac = None
    if extend != 'neither':
        if colorbar.extendfrac is not None: extendfrac = colorbar.extendfrac
        else: extendfrac = 0.05 # From the docs
    
    # Update the figure (required)
    fig.canvas.draw()
    
    # Get ALL the ticks (major AND minor)
    ticks = []
    for child in cax.get_children():
        if type(child).__name__ == 'YAxis':
            for grandchild in child.get_children():
                if type(grandchild).__name__ == 'YTick':
                    if not grandchild.get_visible(): continue
                    tickOns = [grandchild.tick1On, grandchild.tick2On]
                    ticklines = [grandchild.tick1line,grandchild.tick2line]
                    ticklabels = [grandchild.label1.get_text(), grandchild.label2.get_text()]
                    for tickOn,tickline,ticklabel in zip(tickOns,ticklines,ticklabels):
                        if tickOn: ticks.append(tickline.get_ydata()[0])
    
    tick_locs = np.array([tick for tick in sorted(ticks)])
    ticks = tick_locs * (clim[1]-clim[0]) + clim[0]
    colors = [cmap(tick) for tick in tick_locs]
    pos = cax.get_position()
    
    patch_locs = tick_locs
    real_locs = np.array(sorted([patch_loc * (clim[1]-clim[0]) + clim[0] for patch_loc in patch_locs]))
    patches = []

    if extend in ['both','min']:
        verts = np.array([[0.5,-extendfrac],[0.,0.],[1.,0.]])
        patches.append(Polygon(verts,facecolor=cmap(0.)))
    patches.append(Rectangle((0.,0.),1.,patch_locs[0],color=cmap(0.)))
    
    for i,(patch_loc,color) in enumerate(zip(patch_locs[:-1],colors[:-1])):
        patches.append(Rectangle((0.,patch_loc),1.,patch_locs[i+1]-patch_loc,color=color))
    
    patches.append(Rectangle((0.,patch_locs[-1]),1.,1.-patch_locs[-1],color=cmap(1.)))
    if extend in ['both','max']:
        verts = np.array([[0.5,1.+extendfrac],[0.,1.],[1.,1.]])
        patches.append(Polygon(verts,facecolor=cmap(1.)))
    
    p = PatchCollection(patches,match_original=True)
    cax.add_collection(p)

            
    if objects is not None:
        # Flatten the objects if it is an array
        if isinstance(objects,(np.ndarray,list,tuple)): objects = np.concatenate(objects)
        # Turn it into an iterable otherwise
        else: objects = [objects]
        
        for obj in objects:
            objproperties = obj.properties()
            if 'facecolor' in objproperties.keys(): # This is a PatchCollection
                c = objproperties['facecolor']
                
                botcol = cmap(0.)
                all_colors = [botcol] + colors
                for i in range(0,len(all_colors)-1):
                    # In between the colors, there is a difference between the R, G, and B values
                    c0 = all_colors[i]
                    c1 = all_colors[i+1]
                    for col in c:
                        between = [False,False,False]
                        for j in range(0,3): # Check the R, G, and B values
                            between[j] = c0[j] <= col[j] and col[j] < c1[j]
                        if all(between): col = c0
                topcol = cmap(1.)
                for col in c:
                    above = [False,False,False]
                    for j in range(0,3): # Check the R, G, and B values
                        above[j] = col[j] >= topcol[j]
                    if all(above): col = topcol

                obj.set_facecolor(c)
                
            elif 'array' in objproperties.keys() and objproperties['array'] is not None: # Probably an AxesImage
                # In this case, the colors are stored in the actual image data
                print("Warning: imshow detected in make_colorbar_discrete_on_ticks objects. Its data will be edited.")
                arr = objproperties['array']
                data = arr.data
                # We only need to check where the data is between ticks
                for i,row in enumerate(data):
                    for j,col in enumerate(row):
                        if col < ticks[0]: data[i][j] = clim[0]
                        elif col >= ticks[-1]: data[i][j] = clim[1]
                        else:
                            for k in range(0,len(ticks)-1):
                                if ticks[k] <= col and col < ticks[k+1]:
                                    data[i][j] = ticks[k]
                                    break
                obj.set_array(arr)
