<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.10.8-A Coruña" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" minScale="1e+08" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <rasterrenderer type="hillshade" multidirection="0" band="1" azimuth="315" alphaBand="-1" zfactor="1" opacity="1" angle="45">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0"/>
    <huesaturation grayscaleMode="0" colorizeStrength="100" saturation="-2" colorizeRed="255" colorizeBlue="128" colorizeGreen="128" colorizeOn="0"/>
    <rasterresampler zoomedInResampler="bilinear" maxOversampling="2" zoomedOutResampler="bilinear"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
