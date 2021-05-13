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
    from matplotlib.colors import to_rgba,to_rgb,Normalize
    import numpy as np
    from sys import version_info
    
    cax = colorbar.ax
    if version_info.major >= 3:
        cmap = colorbar.cmap
        clim = cax.get_ylim()
    else:
        cmap = colorbar.get_cmap()
        clim = colorbar.get_clim()
    
    extend = colorbar.extend
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
                    if version_info.major < 3:
                        tickOns = [grandchild.tick1On, grandchild.tick2On]
                    else:
                        tickOns = [grandchild.tick1line.get_visible(),grandchild.tick2line.get_visible()]
                    ticklines = [grandchild.tick1line,grandchild.tick2line]
                    ticklabels = [grandchild.label1.get_text(), grandchild.label2.get_text()]
                    for tickOn,tickline,ticklabel in zip(tickOns,ticklines,ticklabels):
                        if tickOn:
                            lw = grandchild._width / 72.
                            lw = cax.transData.inverted().transform(fig.dpi_scale_trans.transform([[0,0],[0.,lw]]))
                            lw = abs(lw[1][1] - lw[0][1])
                            # Not sure why, but adding the full linewidth brings all the rectangles
                            # to half the linewidth, which is what we want.
                            ticks.append(tickline.get_ydata()[0] + lw)
    ticks = sorted(ticks)
    if version_info.major < 3:
        tick_locs = np.array(ticks)
        ticks = tick_locs * (clim[1]-clim[0]) + clim[0]
    else:
        tick_locs = (np.array(ticks) - clim[0]) / (clim[1]-clim[0])
    colors = [cmap(tick_loc) for tick_loc in tick_locs]
    pos = cax.get_position()
    
    patches = []

    if extend in ['both','min']:
        verts = np.array([[0.5,-extendfrac],[0.,0.],[1.,0.]])
        patches.append(Polygon(verts,facecolor=cmap(0.)))
    patches.append(Rectangle((0.,0.),1.,tick_locs[0],color=cmap(0.)))
    
    for i,(tick_loc,color) in enumerate(zip(tick_locs[:-1],colors[:-1])):
        patches.append(Rectangle((0.,tick_loc),1.,tick_locs[i+1]-tick_loc,color=color))
    
    patches.append(Rectangle((0.,tick_locs[-1]),1.,1.-tick_locs[-1],color=cmap(1.)))
    if extend in ['both','max']:
        verts = np.array([[0.5,1.+extendfrac],[0.,1.],[1.,1.]])
        patches.append(Polygon(verts,facecolor=cmap(1.)))
    
    p = PatchCollection(patches,match_original=True)
    if version_info.major >= 3: p.set_transform(cax.transAxes)
    cax.add_collection(p)
    
    if objects is not None:
        # Flatten the objects if it is an array
        # https://stackoverflow.com/a/12474246/4954083
        flatten=lambda l: sum(map(flatten,l),[]) if isinstance(l,(list,tuple,np.ndarray)) else [l]
        if isinstance(objects,(np.ndarray,list,tuple)): objects = flatten(objects)
        # Turn it into an iterable otherwise
        else: objects = [objects]
        #print(objects)
        for q,obj in enumerate(objects):
            objproperties = obj.properties()
            if type(obj).__name__ == 'Line2D':

                def get_value_from_cm(color, cmap, colrange=[0.,1.]):
                    # https://stackoverflow.com/a/45178154/4954083
                    color=to_rgb(color)
                    r = np.linspace(colrange[0],colrange[1], 256)
                    norm = Normalize(colrange[0],colrange[1])
                    mapvals = cmap(norm(r))[:,:3]
                    distance = np.sum((mapvals - color)**2, axis=1)
                    return r[np.argmin(distance)]
                
                c = obj.get_color()
                
                # Check to see if c contains just 1 color. If so, make c iterable
                if not any([isinstance(it,(tuple,list,np.ndarray)) for it in c]): c = [c]

                cmap_locs = [get_value_from_cm(color,cmap) for color in c]
                for i,cmap_loc in enumerate(cmap_locs):
                    if cmap_loc <= tick_locs[0]: cmap_locs[i] = clim[0]
                    elif cmap_loc > tick_locs[-1]: cmap_locs[i] = clim[1]
                    else:
                        for k,tick_loc in enumerate(tick_locs[:-1]):
                            if tick_loc <= cmap_loc and cmap_loc < tick_locs[k+1]:
                                cmap_locs[i] = tick_loc
                                break
                c = [cmap(cmap_loc) for cmap_loc in cmap_locs]
                if len(c) == 1: c = c[0]
                objects[q].set_markerfacecolor(c)
                
            elif 'array' in objproperties.keys() and objproperties['array'] is not None: # Probably an AxesImage
                # In this case, the colors are stored in the actual image data
                arr = objproperties['array']
                data = arr.data
                if type(obj).__name__ == 'AxesImage':
                    print("Warning: imshow detected in make_colorbar_discrete_on_ticks objects. Its data will be edited.")
                    # We only need to check where the data is between ticks
                    for i,row in enumerate(data):
                        for j,col in enumerate(row):
                            if col < min(ticks): data[i][j] = min(clim)
                            elif col >= max(ticks): data[i][j] = max(clim)
                            else:
                                for k in range(0,len(ticks)-1):
                                    if ticks[k] < ticks[k+1]:
                                        smaller = ticks[k]
                                        larger = ticks[k+1]
                                    else:
                                        smaller = ticks[k+1]
                                        larger = ticks[k]
                                    if smaller <= col and col < larger:
                                        data[i][j] = smaller
                                        break
                elif type(obj).__name__ == 'PathCollection':
                    data = arr.data.ravel()
                    for i,element in enumerate(data):
                        if element < ticks[0]: data[i] = clim[0]
                        elif element >= ticks[-1]: data[i] = clim[1]
                        else:
                            for k in range(0,len(ticks)-1):
                                if ticks[k] <= element and element < ticks[k+1]:
                                    data[i] = ticks[k]
                                    break
                else:
                    raise Exception("Object type '"+type(obj).__name__+"' not supported")

                obj.set_array(arr)
