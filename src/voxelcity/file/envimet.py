import os
import numpy as np
import datetime

from ..geo.grid import apply_operation, translate_array, group_and_label_cells, process_grid
from ..geo.utils import get_city_country_name_from_rectangle, get_timezone_info
from ..utils.lc import convert_land_cover

def array_to_string(arr):
    return '\n'.join('     ' + ','.join(str(cell) for cell in row) for row in arr)

def array_to_string_with_value(arr, value):
    return '\n'.join('     ' + ','.join(str(value) for cell in row) for row in arr)

def array_to_string_int(arr):
    return '\n'.join('     ' + ','.join(str(int(cell+0.5)) for cell in row) for row in arr)

def prepare_grids(building_height_grid_ori, building_id_grid_ori, canopy_height_grid_ori, land_cover_grid_ori, dem_grid_ori, meshsize, land_cover_source):
    building_height_grid = np.flipud(np.nan_to_num(building_height_grid_ori, nan=10.0)).copy()#set 10m height to nan
    building_id_grid = np.flipud(building_id_grid_ori)
    building_height_grid[0, :] = building_height_grid[-1, :] = building_height_grid[:, 0] = building_height_grid[:, -1] = 0
    building_height_grid = apply_operation(building_height_grid, meshsize)

    if (land_cover_source == 'OpenEarthMapJapan') or (land_cover_source == 'OpenStreetMap'):
        land_cover_grid_converted = land_cover_grid_ori   
    else:
        land_cover_grid_converted = convert_land_cover(land_cover_grid_ori, land_cover_source=land_cover_source)        

    land_cover_grid = np.flipud(land_cover_grid_converted).copy() + 1

    veg_translation_dict = {
        1: '',
        2: '0200XX',
        3: '',
        4: '',
        5: '0200XX',
        6: '',
        7: '0200XX',
        8: ''
    }
    land_cover_veg_grid = translate_array(land_cover_grid, veg_translation_dict)

    mat_translation_dict = {
        1: '000000',#'Bareland',
        2: '000000',#'Rangeland',
        3: '000000',#'Shrub',
        4: '000000',#'Moss and lichen',
        5: '000000',#'Agriculture land',
        6: '000000',#'Tree',
        7: '0200WW',#'Wet land',
        8: '0200WW',#'Mangroves',
        9: '0200WW',#'Water',
        10: '000000',#'Snow and ice',
        11: '0200PG',#'Developed space',
        12: '0200ST',#'Road',
        13: '000000',#'Building',
        14: '0200SD',#'No Data'
    }
    land_cover_mat_grid = translate_array(land_cover_grid, mat_translation_dict)

    # canopy_height_grid = np.flipud(canopy_height_grid_ori).copy()
    canopy_height_grid = canopy_height_grid_ori.copy()

    dem_grid = np.flipud(dem_grid_ori).copy() - np.min(dem_grid_ori)

    return building_height_grid, building_id_grid, land_cover_veg_grid, land_cover_mat_grid, canopy_height_grid, dem_grid

def create_xml_content(building_height_grid, building_id_grid, land_cover_veg_grid, land_cover_mat_grid, canopy_height_grid, dem_grid, meshsize, rectangle_vertices, **kwargs):
    # XML template
    xml_template = """<ENVI-MET_Datafile>
    <Header>
    <filetype>INPX ENVI-met Area Input File</filetype>
    <version>440</version>
    <revisiondate>7/5/2024 5:44:52 PM</revisiondate>
    <remark>Created with SPACES 5.6.1</remark>
    <checksum>0</checksum>
    <encryptionlevel>0</encryptionlevel>
    </Header>
      <baseData>
         <modelDescription> $modelDescription$ </modelDescription>
         <modelAuthor> $modelAuthor$ </modelAuthor>
         <modelcopyright> The creator or distributor is responsible for following Copyright Laws </modelcopyright>
      </baseData>
      <modelGeometry>
         <grids-I> $grids-I$ </grids-I>
         <grids-J> $grids-J$ </grids-J>
         <grids-Z> $grids-Z$ </grids-Z>
         <dx> $dx$ </dx>
         <dy> $dy$ </dy>
         <dz-base> $dz-base$ </dz-base>
         <useTelescoping_grid> $useTelescoping_grid$ </useTelescoping_grid>
         <useSplitting> 1 </useSplitting>
         <verticalStretch> $verticalStretch$ </verticalStretch>
         <startStretch> $startStretch$ </startStretch>
         <has3DModel> 0 </has3DModel>
         <isFull3DDesign> 0 </isFull3DDesign>
      </modelGeometry>
      <nestingArea>
         <numberNestinggrids> 0 </numberNestinggrids>
         <soilProfileA> 000000 </soilProfileA>
         <soilProfileB> 000000 </soilProfileB>
      </nestingArea>
      <locationData>
         <modelRotation> $modelRotation$ </modelRotation>
         <projectionSystem> $projectionSystem$ </projectionSystem>
         <UTMZone> 0 </UTMZone>
         <realworldLowerLeft_X> 0.00000 </realworldLowerLeft_X>
         <realworldLowerLeft_Y> 0.00000 </realworldLowerLeft_Y>
         <locationName> $locationName$ </locationName>
         <location_Longitude> $location_Longitude$ </location_Longitude>
         <location_Latitude> $location_Latitude$ </location_Latitude>
         <locationTimeZone_Name> $locationTimeZone_Name$ </locationTimeZone_Name>
         <locationTimeZone_Longitude> $locationTimeZone_Longitude$ </locationTimeZone_Longitude>
      </locationData>
      <defaultSettings>
         <commonWallMaterial> 000000 </commonWallMaterial>
         <commonRoofMaterial> 000000 </commonRoofMaterial>
      </defaultSettings>
      <buildings2D>
         <zTop type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $zTop$
         </zTop>
         <zBottom type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $zBottom$
         </zBottom>
         <buildingNr type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $buildingNr$
         </buildingNr>
         <fixedheight type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $fixedheight$
         </fixedheight>
      </buildings2D>
      <simpleplants2D>
         <ID_plants1D type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $ID_plants1D$
         </ID_plants1D>
      </simpleplants2D>
    $3Dplants$
      <soils2D>
         <ID_soilprofile type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $ID_soilprofile$
         </ID_soilprofile>
      </soils2D>
      <dem>
         <DEMReference> $DEMReference$ </DEMReference>
         <terrainheight type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $terrainheight$
         </terrainheight>
      </dem>
      <sources2D>
         <ID_sources type="matrix-data" dataI="$grids-I$" dataJ="$grids-J$">
    $ID_sources$
         </ID_sources>
      </sources2D>
    </ENVI-MET_Datafile>"""

    
    city_country_name = get_city_country_name_from_rectangle(rectangle_vertices)

    # Calculate the center point of the rectangle
    latitudes = [coord[0] for coord in rectangle_vertices]
    longitudes = [coord[1] for coord in rectangle_vertices]
    center_lat = str(sum(latitudes) / len(latitudes))
    center_lon = str(sum(longitudes) / len(longitudes))
    
    timezone_info = get_timezone_info(rectangle_vertices)

    author_name = kwargs.get('author_name')
    if author_name is None:
        author_name = "[Enter model author name]"
    model_desctiption = kwargs.get('model_desctiption')
    if model_desctiption is None:
        model_desctiption = "[Enter model desctription]"

    # Replace placeholders
    placeholders = {
        "$modelDescription$": model_desctiption,
        "$modelAuthor$": author_name,
        "$modelRotation$": "0",
        "$projectionSystem$": "GCS_WGS_1984",
        "$locationName$": city_country_name,
        "$location_Longitude$": center_lon,
        "$location_Latitude$": center_lat,
        "$locationTimeZone_Name$": timezone_info[0],
        "$locationTimeZone_Longitude$": timezone_info[1],
    }

    for placeholder, value in placeholders.items():
        xml_template = xml_template.replace(placeholder, value)
    
    building_on_dem_grid = building_height_grid + dem_grid    
    
    domain_building_max_height_ratio = kwargs.get('domain_building_max_height_ratio')
    if domain_building_max_height_ratio is None:
        domain_building_max_height_ratio = 2
    useTelescoping_grid = kwargs.get('useTelescoping_grid')
    if (useTelescoping_grid is None) or (useTelescoping_grid == False):
        useTelescoping_grid = 0
        verticalStretch = 0
        startStretch = 0
    else:
        useTelescoping_grid = 1
        verticalStretch = kwargs.get('verticalStretch')
        if (verticalStretch is None):
            verticalStretch = 20
        startStretch = kwargs.get('startStretch')
        if (startStretch is None):
            startStretch = int(np.max(building_on_dem_grid)/meshsize + 0.5) * meshsize
    
    # Set grid dimensions
    grids_I, grids_J = building_height_grid.shape[1], building_height_grid.shape[0]


    min_grids_Z = kwargs.get('min_grids_Z')
    if verticalStretch > 0:
        a = meshsize
        r = (100 + verticalStretch) / 100
        S_target = (int(np.max(building_on_dem_grid)/meshsize + 0.5) * meshsize) * (domain_building_max_height_ratio - 1)
        min_n = find_min_n(a, r, S_target, max_n=1000000)
        grids_Z_tent = int(np.max(building_on_dem_grid)/meshsize + 0.5) + min_n
        if grids_Z_tent < min_grids_Z:
            grids_Z = min_grids_Z
            startStretch += (min_grids_Z - grids_Z)
        else:
            grids_Z = grids_Z_tent
    else:
        grids_Z = max(int(np.max(building_on_dem_grid)/meshsize + 0.5) * domain_building_max_height_ratio, min_grids_Z)

    dx, dy, dz_base = meshsize, meshsize, meshsize

    grid_placeholders = {
        "$grids-I$": str(grids_I),
        "$grids-J$": str(grids_J),
        "$grids-Z$": str(grids_Z),
        "$dx$": str(dx),
        "$dy$": str(dy),
        "$dz-base$": str(dz_base),
        "$useTelescoping_grid$": str(useTelescoping_grid),
        "$verticalStretch$": str(verticalStretch),
        "$startStretch$": str(startStretch),
    }

    for placeholder, value in grid_placeholders.items():
        xml_template = xml_template.replace(placeholder, value)

    # Replace matrix data
    xml_template = xml_template.replace("$zTop$", array_to_string(building_height_grid))
    xml_template = xml_template.replace("$zBottom$", array_to_string_with_value(building_height_grid, '0'))
    xml_template = xml_template.replace("$fixedheight$", array_to_string_with_value(building_height_grid, '0'))

    building_nr_grid = group_and_label_cells(building_id_grid)
    xml_template = xml_template.replace("$buildingNr$", array_to_string(building_nr_grid))

    xml_template = xml_template.replace("$ID_plants1D$", array_to_string(land_cover_veg_grid))

    # Add 3D plants
    tree_content = ""
    for i in range(grids_I):
        for j in range(grids_J):
            canopy_height = int(canopy_height_grid[j, i] + 0.5)
            if canopy_height_grid[j, i] > 0 and np.flipud(building_height_grid)[j, i]==0:
            # if canopy_height > 0 and building_height_grid[j, i]==0:
                plantid = f'H{canopy_height:02d}W01'
                tree_ij = f"""  <3Dplants>
     <rootcell_i> {i+1} </rootcell_i>
     <rootcell_j> {j+1} </rootcell_j>
     <rootcell_k> 0 </rootcell_k>
     <plantID> {plantid} </plantID>
     <name> .{plantid} </name>
     <observe> 0 </observe>
  </3Dplants>"""
                tree_content += '\n' + tree_ij

    xml_template = xml_template.replace("$3Dplants$", tree_content)
    xml_template = xml_template.replace("$ID_soilprofile$", array_to_string(land_cover_mat_grid))
    dem_grid = process_grid(building_nr_grid, dem_grid)
    xml_template = xml_template.replace("$DEMReference$", '0')
    xml_template = xml_template.replace("$terrainheight$", array_to_string_int(dem_grid))
    xml_template = xml_template.replace("$ID_sources$", array_to_string_with_value(land_cover_mat_grid, ''))

    return xml_template

def save_file(content, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def export_inx(building_height_grid_ori, building_id_grid_ori, canopy_height_grid_ori, land_cover_grid_ori, dem_grid_ori, meshsize, land_cover_source, rectangle_vertices, **kwargs):
    # Prepare grids
    building_height_grid_inx, building_id_grid, land_cover_veg_grid_inx, land_cover_mat_grid_inx, canopy_height_grid_inx, dem_grid_inx = prepare_grids(
        building_height_grid_ori.copy(), building_id_grid_ori.copy(), canopy_height_grid_ori.copy(), land_cover_grid_ori.copy(), dem_grid_ori.copy(), meshsize, land_cover_source)    

    # Create XML content
    xml_content = create_xml_content(building_height_grid_inx, building_id_grid, land_cover_veg_grid_inx, land_cover_mat_grid_inx, canopy_height_grid_inx, dem_grid_inx, meshsize, rectangle_vertices, **kwargs)

    # Save the output
    output_dir = kwargs.get("output_directory", 'output')
    output_file_path = os.path.join(output_dir, "output.INX")
    save_file(xml_content, output_file_path)

def generate_edb_file(**kwargs):
    
    lad = kwargs.get('lad')
    if lad is None:
        lad=1.0
    
    trunk_height_ratio = kwargs.get("trunk_height_ratio")
    if trunk_height_ratio is None:
        trunk_height_ratio = 11.76 / 19.98

    header = f'''<ENVI-MET_Datafile>
<Header>
<filetype>DATA</filetype>
<version>1</version>
<revisiondate>{datetime.datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")}</revisiondate>
<remark>Envi-Data</remark>
<checksum>0</checksum>
<encryptionlevel>1699612</encryptionlevel>
</Header>
'''

    footer = '</ENVI-MET_Datafile>'

    plant3d_objects = []

    for height in range(1, 51):
        plant3d = f'''  <PLANT3D>
     <ID> H{height:02d}W01 </ID>
     <Description> H{height:02d}W01 </Description>
     <AlternativeName> Albero nuovo </AlternativeName>
     <Planttype> 0 </Planttype>
     <Leaftype> 1 </Leaftype>
     <Albedo> 0.18000 </Albedo>
     <Eps> 0.00000 </Eps>
     <Transmittance> 0.30000 </Transmittance>
     <isoprene> 12.00000 </isoprene>
     <leafweigth> 100.00000 </leafweigth>
     <rs_min> 0.00000 </rs_min>
     <Height> {height:.5f} </Height>
     <Width> 1.00000 </Width>
     <Depth> {height * trunk_height_ratio:.5f} </Depth>
     <RootDiameter> 1.00000 </RootDiameter>
     <cellsize> 1.00000 </cellsize>
     <xy_cells> 1 </xy_cells>
     <z_cells> {height} </z_cells>
     <scalefactor> 0.00000 </scalefactor>
     <LAD-Profile type="sparematrix-3D" dataI="1" dataJ="1" zlayers="{height}" defaultValue="0.00000">
{generate_lad_profile(height, trunk_height_ratio, lad=str(lad))}
     </LAD-Profile>
     <RAD-Profile> 0.10000,0.10000,0.10000,0.10000,0.10000,0.10000,0.10000,0.10000,0.10000,0.10000 </RAD-Profile>
     <Root-Range-Profile> 1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,1.00000 </Root-Range-Profile>
     <Season-Profile> 0.30000,0.30000,0.30000,0.40000,0.70000,1.00000,1.00000,1.00000,0.80000,0.60000,0.30000,0.30000 </Season-Profile>
     <Blossom-Profile> 0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000 </Blossom-Profile>
     <DensityWood> 690.00000 </DensityWood>
     <YoungsModulus> 8770000896.00000 </YoungsModulus>
     <YoungRatioRtoL> 0.12000 </YoungRatioRtoL>
     <MORBranch> 65.00000 </MORBranch>
     <MORConnection> 45.00000 </MORConnection>
     <PlantGroup> 0 </PlantGroup>
     <Color> 0 </Color>
     <Group>  </Group>
     <Author>  </Author>
     <costs> 0.00000 </costs>
     <ColorStem> 0 </ColorStem>
     <ColorBlossom> 0 </ColorBlossom>
     <BlossomRadius> 0.00000 </BlossomRadius>
     <L-SystemBased> 0 </L-SystemBased>
     <Axiom> V </Axiom>
     <IterationDepth> 0 </IterationDepth>
     <hasUserEdits> 0 </hasUserEdits>
     <LADMatrix_generated> 0 </LADMatrix_generated>
     <InitialSegmentLength> 0.00000 </InitialSegmentLength>
     <SmallSegmentLength> 0.00000 </SmallSegmentLength>
     <ChangeSegmentLength> 0.00000 </ChangeSegmentLength>
     <SegmentResolution> 0.00000 </SegmentResolution>
     <TurtleAngle> 0.00000 </TurtleAngle>
     <RadiusOuterBranch> 0.00000 </RadiusOuterBranch>
     <PipeFactor> 0.00000 </PipeFactor>
     <LeafPosition> 0 </LeafPosition>
     <LeafsPerNode> 0 </LeafsPerNode>
     <LeafInternodeLength> 0.00000 </LeafInternodeLength>
     <LeafMinSegmentOrder> 0 </LeafMinSegmentOrder>
     <LeafWidth> 0.00000 </LeafWidth>
     <LeafLength> 0.00000 </LeafLength>
     <LeafSurface> 0.00000 </LeafSurface>
     <PetioleAngle> 0.00000 </PetioleAngle>
     <PetioleLength> 0.00000 </PetioleLength>
     <LeafRotationalAngle> 0.00000 </LeafRotationalAngle>
     <FactorHorizontal> 0.00000 </FactorHorizontal>
     <TropismVector> 0.000000,0.000000,0.000000 </TropismVector>
     <TropismElstaicity> 0.00000 </TropismElstaicity>
     <SegmentRemovallist>  </SegmentRemovallist>
     <NrRules> 0 </NrRules>
     <Rules_Variable>  </Rules_Variable>
     <Rules_Replacement>  </Rules_Replacement>
     <Rules_isConditional>  </Rules_isConditional>
     <Rules_Condition>  </Rules_Condition>
     <Rules_Remark>  </Rules_Remark>
     <TermLString>   </TermLString>
     <ApplyTermLString> 0 </ApplyTermLString>
  </PLANT3D>
'''
        plant3d_objects.append(plant3d)

    content = header + ''.join(plant3d_objects) + footer
    
    with open('projectdatabase.edb', 'w') as f:
        f.write(content)

def generate_lad_profile(height, trunk_height_ratio, lad = '1.00000'):
    lad_profile = []
    start = max(0, int(height * trunk_height_ratio))
    for i in range(start, height):
        lad_profile.append(f"     0,0,{i},{lad}")
    return '\n'.join(lad_profile)
    
def find_min_n(a, r, S_target, max_n=1000000):
    n = 1
    while n <= max_n:
        if r == 1:
            S_n = a * n
        else:
            try:
                S_n = a * (1 - r ** n) / (1 - r)
            except OverflowError:
                # Handle large exponents
                S_n = float('inf') if r > 1 else 0
        if (a > 0 and S_n > S_target) or (a < 0 and S_n < S_target):
            return n
        n += 1
    return None  # Not possible within max_n terms