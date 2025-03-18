from opentrons import protocol_api

color_slots = ['7','8','9']
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

metadata = {
    'protocolName': 'Color Matching v0.2',
    'author': 'CMU Automated Lab',
    'description': 'Attempts to robotically match colors using active learning.',
}

requirements = {'robotType': 'OT-2', 'apiLevel': '2.19'}


def run(protocol: protocol_api.ProtocolContext) -> None:
    """Defines the testing protocol."""

    class Well:
        """
        Represents a well on a plate.
        """
        def __init__(self, max_volume: float, volume: float = 0):
            self.max_volume = max_volume
            self.volume = volume

    class Plate:
        """
        Represents a plate with wells.
        """
        def __init__(self, labware: protocol_api.Labware, rows: int, columns: int, well_max_volume: float):
            self.labware = labware
            self.rows = rows
            self.columns = columns
            self.wells = {f"{ascii_uppercase[row]}{column + 1}": Well(well_max_volume) for row in range(rows) for column in range(columns)}

        def get_well(self, row: int, column: int) -> Well:
            return self.wells[row][column]

    def setup(plate_type: str = "corning_96_wellplate_360ul_flat") -> tuple[dict[str, protocol_api.Labware], Plate, protocol_api.InstrumentContext]:
        """
        Loads labware and instruments for the protocol.

        :param plate_type: The type of plate to use, as per the Opentrons API.
        """
        tipracks: list[protocol_api.Labware] = [protocol.load_labware('opentrons_96_tiprack_300ul', location='3')]

        colors: dict[str, protocol_api.Labware] = {}
        for slot in color_slots:
            colors[slot] = protocol.load_labware('nest_1_reservoir_290ml', location=str(slot))['A1']

        plate_labware = protocol.load_labware(plate_type, label="Dye Plate", location='1')
        plate = Plate(plate_labware, len(plate_labware.rows()), len(plate_labware.columns()), plate_labware.wells()[0].max_volume)

        pipette = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=tipracks)

        return colors, plate, pipette
    
    def get_plate_type() -> str:
        """
        Uses the attached camera to determine the type of plate being used.
        """
        raise NotImplementedError

    #plate_type = get_plate_type()
    plate_type = "corning_96_wellplate_360ul_flat" # TODO: Remove this line when get_plate_type is implemented.
    colors, plate, pipette = setup(plate_type)

    def get_color() -> list[list[list[float]]]:
        """
        Uses the attached camera to determine the color of the dye in each well on the plate.

        :return: An array of RGB values for each well on the plate.
        """
        raise NotImplementedError

    def add_color(
            color_slot: str | int,
            plate_well: str,
            volume: float) -> None:
        """
        Adds a color to the plate at the specified well.

        :param color_slot: The slot of the color reservoir.
        :param plate_well: The well of the plate to add the color to.
        :param volume: The volume of the color to add.

        :raises ValueError: If the well is already full.
        """
        if volume + plate.wells[plate_well].volume > plate.wells[plate_well].max_volume:
            raise ValueError("Cannot add color to well; well is full.")

        pipette.pick_up_tip()
        pipette.aspirate(volume, colors[color_slot])
        pipette.touch_tip(plate.labware[plate_well], v_offset=95, radius=0) # necessary to avoid crashing against the large adapter
        pipette.dispense(volume, plate.labware[plate_well].bottom(z=81))

        plate.wells[plate_well].volume += volume

        # Quick mix (has to be manual because the default mix function doesn't work with the large adapter)
        pipette.aspirate(volume/2, plate.labware[plate_well].bottom(z=81))
        pipette.dispense(volume/2, plate.labware[plate_well].bottom(z=81))
        pipette.aspirate(volume/2, plate.labware[plate_well].bottom(z=81))
        pipette.dispense(volume/2, plate.labware[plate_well].bottom(z=81))

        pipette.drop_tip()


    # TESTING
    add_color('7', 'A1', 100)
    add_color('8', 'A1', 200)
    add_color('9', 'A2', 300)

    return 

    def active_learning() -> None:
        """
        The main loop of the protocol, which uses active learning to determine the best color match.
        """
        raise NotImplementedError

    # Main Loop
    i = 0
    while not active_learning():
        print(f"Active Learning Iteration {i}")
        i += 1
    print("Color Matching Complete.")