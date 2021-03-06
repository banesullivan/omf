"""lineset.py: LineSet element and geometry"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import properties

from .base import ProjectElement, ProjectElementGeometry
from .data import Int2Array, Vector3Array


class LineSetGeometry(ProjectElementGeometry):
    """Contains spatial information of a line set"""
    vertices = properties.Instance(
        'Spatial coordinates of line vertices relative to line set origin',
        Vector3Array
    )
    segments = properties.Instance(
        'Endpoint vertex indices of line segments',
        Int2Array
    )

    _valid_locations = ('vertices', 'segments')

    def location_length(self, location):
        """Return correct data length based on location"""
        if location == 'segments':
            return self.num_cells
        return self.num_nodes

    @property
    def num_nodes(self):
        """Number of nodes (vertices)"""
        return len(self.vertices)

    @property
    def num_cells(self):
        """Number of cells (segments)"""
        return len(self.segments)

    @properties.validator
    def _validate_mesh(self):
        """Ensures segment indices are valid"""
        if np.min(self.segments) < 0:
            raise ValueError('Segments may only have positive integers')
        if np.max(self.segments) >= len(self.vertices):
            raise ValueError('Segments expects more vertices than provided')
        return True


class LineSetElement(ProjectElement):
    """Contains mesh, data, and options of a line set"""
    geometry = properties.Instance(
        'Structure of the line element',
        instance_class=LineSetGeometry
    )
    subtype = properties.StringChoice(
        'Category of LineSet',
        choices=('line', 'borehole'),
        default='line'
    )

    def toVTK(self):
        """Convert the line set to a ``vtkPloyData`` data object."""
        import vtk
        from vtk.util import numpy_support as nps

        output = vtk.vtkPolyData()
        cells = vtk.vtkCellArray()
        pts = vtk.vtkPoints()

        # Make a data array for grouping the line segments
        indexArr = vtk.vtkIntArray()
        indexArr.SetNumberOfValues(self.geometry.num_cells)
        indexArr.SetName('Line Index')

        # Generate VTK Points from the vertices
        pts.SetNumberOfPoints(self.geometry.num_nodes)
        pts.SetData(nps.numpy_to_vtk(self.geometry.vertices))

        last = self.geometry.segments[0][0]
        segi = 0
        for i in range(len(self.geometry.segments)):
            # Create a VTK Line cell for each segment
            seg = self.geometry.segments[i]
            aLine = vtk.vtkLine()
            aLine.GetPointIds().SetId(0, seg[0])
            aLine.GetPointIds().SetId(1, seg[1])
            cells.InsertNextCell(aLine)
            # Group segments by connectivity:
            if seg[0] != last:
                segi += 1
            last = seg[1]
            indexArr.SetValue(i, segi)

        # Generate the output
        output.SetPoints(pts)
        output.SetLines(cells)
        output.GetCellData().AddArray(indexArr)

        # Now add data to lines:
        for data in self.data:
            arr = data.array.array
            c = nps.numpy_to_vtk(num_array=arr)
            c.SetName(data.name)
            output.GetCellData().AddArray(c)

        # TODO: if subtype is borehole make a tube

        return output
