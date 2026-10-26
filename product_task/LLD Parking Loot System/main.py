from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
import math


# ============================================================
# 1. VEHICLE TYPE
# ============================================================

class VehicleType(Enum):
    BIKE = "BIKE"
    CAR = "CAR"
    TRUCK = "TRUCK"


# ============================================================
# 2. VEHICLE
# ============================================================

class Vehicle:

    def __init__(self, license_plate, vehicle_type):
        if not isinstance(vehicle_type, VehicleType):
            raise ValueError("Invalid vehicle type.")

        if not isinstance(license_plate, str) or not license_plate.strip():
            raise ValueError("License plate cannot be empty.")

        self.license_plate = license_plate.strip()
        self.vehicle_type = vehicle_type

    def __str__(self):
        return f"{self.license_plate} ({self.vehicle_type.value})"


# ============================================================
# 3. VEHICLE FACTORY
# Factory Pattern
# ============================================================

class VehicleFactory:

    @staticmethod
    def create_vehicle(license_plate, vehicle_type):
        return Vehicle(license_plate, vehicle_type)


# ============================================================
# 4. PARKING SLOT
# ============================================================

class ParkingSlot:

    def __init__(self, slot_id, vehicle_type):
        self.slot_id = slot_id
        self.vehicle_type = vehicle_type
        self.vehicle = None

    def can_fit(self, vehicle_type):
        return (
            self.vehicle is None
            and self.vehicle_type == vehicle_type
        )

    def assign_vehicle(self, vehicle):
        if vehicle.vehicle_type != self.vehicle_type:
            raise ValueError("This slot does not support the vehicle type.")

        if not self.is_available():
            raise ValueError("This parking slot is already occupied.")

        self.vehicle = vehicle

    def remove_vehicle(self):
        self.vehicle = None

    def is_available(self):
        return self.vehicle is None


# ============================================================
# 5. PARKING FLOOR
# ============================================================

class ParkingFloor:

    def __init__(self, floor_number):
        self.floor_number = floor_number
        self.slots = []

    def add_slot(self, slot):
        self.slots.append(slot)

    def find_available_slot(self, vehicle_type):

        for slot in self.slots:

            if slot.can_fit(vehicle_type):
                return slot

        return None

    def get_available_slots(self, vehicle_type):

        available_slots = []

        for slot in self.slots:

            if slot.can_fit(vehicle_type):
                available_slots.append(slot)

        return available_slots

    def display_occupancy(self):

        print(f"\nFloor {self.floor_number}")

        for slot in self.slots:

            if slot.is_available():

                print(
                    f"  {slot.slot_id} "
                    f"({slot.vehicle_type.value}) -> FREE"
                )

            else:

                print(
                    f"  {slot.slot_id} "
                    f"({slot.vehicle_type.value}) -> "
                    f"OCCUPIED by "
                    f"{slot.vehicle.license_plate}"
                )


# ============================================================
# 6. PARKING LOT
# ============================================================

class ParkingLot:

    def __init__(self):
        self.floors = []

    def add_floor(self, floor):
        self.floors.append(floor)

    def get_available_slots(self, vehicle_type):

        available_slots = []

        for floor in self.floors:

            available_slots.extend(
                floor.get_available_slots(vehicle_type)
            )

        return available_slots

    def display_occupancy(self):

        print("\n========== PARKING OCCUPANCY ==========")

        for floor in self.floors:
            floor.display_occupancy()

        print("=======================================")


def parse_vehicle_type(value):
    normalized = str(value).strip().lower()

    mapping = {
        "bike": VehicleType.BIKE,
        "b": VehicleType.BIKE,
        "car": VehicleType.CAR,
        "c": VehicleType.CAR,
        "truck": VehicleType.TRUCK,
        "t": VehicleType.TRUCK,
    }

    if normalized not in mapping:
        raise ValueError(
            "Invalid vehicle type. Choose bike, car or truck."
        )

    return mapping[normalized]


def build_parking_lot():
    parking_lot = ParkingLot()

    floor1 = ParkingFloor(1)
    floor1.add_slot(ParkingSlot("F1-B1", VehicleType.BIKE))
    floor1.add_slot(ParkingSlot("F1-C1", VehicleType.CAR))
    floor1.add_slot(ParkingSlot("F1-T1", VehicleType.TRUCK))

    floor2 = ParkingFloor(2)
    floor2.add_slot(ParkingSlot("F2-B1", VehicleType.BIKE))
    floor2.add_slot(ParkingSlot("F2-C1", VehicleType.CAR))

    parking_lot.add_floor(floor1)
    parking_lot.add_floor(floor2)

    return parking_lot


# ============================================================
# 7. TICKET
# ============================================================

class Ticket:

    def __init__(self, ticket_id, vehicle, slot):

        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.slot = slot

        self.entry_time = datetime.now()
        self.exit_time = None
        self.fee = 0

    def close_ticket(self, fee):

        self.exit_time = datetime.now()
        self.fee = fee

    def is_active(self):

        return self.exit_time is None


# ============================================================
# 8. SLOT ALLOCATION STRATEGY
# Strategy Pattern
# ============================================================

class SlotAllocationStrategy(ABC):

    @abstractmethod
    def find_slot(self, parking_lot, vehicle):
        pass


# ============================================================
# 9. FIRST AVAILABLE SLOT STRATEGY
# ============================================================

class FirstAvailableSlotStrategy(SlotAllocationStrategy):

    def find_slot(self, parking_lot, vehicle):

        for floor in parking_lot.floors:

            slot = floor.find_available_slot(
                vehicle.vehicle_type
            )

            if slot is not None:
                return slot

        return None


# ============================================================
# 10. FEE STRATEGY
# Strategy Pattern
# ============================================================

class FeeStrategy(ABC):

    @abstractmethod
    def calculate_fee(self, ticket):
        pass


# ============================================================
# 11. HOURLY FEE STRATEGY
# ============================================================

class HourlyFeeStrategy(FeeStrategy):

    def __init__(self):

        self.rates = {
            VehicleType.BIKE: 20,
            VehicleType.CAR: 40,
            VehicleType.TRUCK: 60
        }

    def calculate_fee(self, ticket):

        current_time = datetime.now()

        duration = (
            current_time - ticket.entry_time
        )

        minutes = duration.total_seconds() / 60

        # Minimum 1 hour charge
        hours = max(
            1,
            math.ceil(minutes / 60)
        )

        rate = self.rates[
            ticket.vehicle.vehicle_type
        ]

        return hours * rate


# ============================================================
# 12. PARKING SERVICE
# Service / Controller Layer
# ============================================================

class ParkingService:

    def __init__(
        self,
        parking_lot,
        allocation_strategy,
        fee_strategy
    ):

        self.parking_lot = parking_lot

        self.allocation_strategy = (
            allocation_strategy
        )

        self.fee_strategy = fee_strategy

        # ticket_id -> Ticket
        self.tickets = {}

        # Store license plates of currently parked vehicles
        self.parked_vehicles = set()

        self.ticket_counter = 1


    # ========================================================
    # PARK VEHICLE
    # ========================================================

    def park_vehicle(self, vehicle):

        if not isinstance(vehicle.vehicle_type, VehicleType):
            print("ERROR: Invalid vehicle type.")
            return None

        print(
            f"\nTrying to park: {vehicle}"
        )

        # ----------------------------------------------------
        # Validate duplicate vehicle
        # ----------------------------------------------------

        vehicle_key = vehicle.license_plate.casefold()

        if vehicle_key in self.parked_vehicles:

            print(
                "ERROR: Vehicle is already parked."
            )

            return None


        # ----------------------------------------------------
        # Find suitable slot using Strategy
        # ----------------------------------------------------

        slot = self.allocation_strategy.find_slot(
            self.parking_lot,
            vehicle
        )


        # ----------------------------------------------------
        # Check slot availability
        # ----------------------------------------------------

        if slot is None:

            print(
                f"ERROR: No slot available for "
                f"{vehicle.vehicle_type.value}."
            )

            return None

        if not slot.can_fit(vehicle.vehicle_type):
            print("ERROR: No suitable slot is available.")
            return None


        # ----------------------------------------------------
        # Assign vehicle to slot
        # ----------------------------------------------------

        slot.assign_vehicle(vehicle)


        # ----------------------------------------------------
        # Generate ticket
        # ----------------------------------------------------

        ticket_id = f"T{self.ticket_counter}"

        self.ticket_counter += 1


        ticket = Ticket(
            ticket_id,
            vehicle,
            slot
        )


        # Store ticket
        self.tickets[ticket_id] = ticket


        # Store parked vehicle
        self.parked_vehicles.add(
            vehicle_key
        )


        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        print(
            "Vehicle parked successfully."
        )

        print(
            f"Ticket : {ticket_id}"
        )

        print(
            f"Slot   : {slot.slot_id}"
        )

        print(
            f"Floor  : {self.get_floor_number(slot)}"
        )

        return ticket


    # ========================================================
    # GET FLOOR NUMBER
    # ========================================================

    def get_floor_number(self, target_slot):

        for floor in self.parking_lot.floors:

            if target_slot in floor.slots:
                return floor.floor_number

        return None


    # ========================================================
    # UNPARK VEHICLE
    # ========================================================

    def unpark_vehicle(self, ticket_id):

        print(
            f"\nTrying to exit using ticket: {ticket_id}"
        )


        # ----------------------------------------------------
        # Validate ticket
        # ----------------------------------------------------

        if not isinstance(ticket_id, str) or ticket_id not in self.tickets:

            print(
                "ERROR: Invalid ticket."
            )

            return


        ticket = self.tickets[ticket_id]


        # ----------------------------------------------------
        # Check repeated exit
        # ----------------------------------------------------

        if not ticket.is_active():

            print(
                "ERROR: Vehicle has already exited."
            )

            return


        # ----------------------------------------------------
        # Calculate fee
        # ----------------------------------------------------

        fee = self.fee_strategy.calculate_fee(
            ticket
        )


        # ----------------------------------------------------
        # Close ticket
        # ----------------------------------------------------

        ticket.close_ticket(fee)


        # ----------------------------------------------------
        # Release slot
        # ----------------------------------------------------

        ticket.slot.remove_vehicle()


        # ----------------------------------------------------
        # Remove vehicle from parked vehicles
        # ----------------------------------------------------

        self.parked_vehicles.remove(
            ticket.vehicle.license_plate.casefold()
        )


        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        print(
            "Vehicle exited successfully."
        )

        print(
            f"Vehicle: {ticket.vehicle}"
        )

        print(
            f"Slot   : {ticket.slot.slot_id}"
        )

        print(
            f"Fee    : ₹{fee}"
        )


    # ========================================================
    # VIEW AVAILABLE SLOTS
    # ========================================================

    def get_available_slots(self, vehicle_type):

        if not isinstance(vehicle_type, VehicleType):
            print("ERROR: Invalid vehicle type.")
            return []

        slots = self.parking_lot.get_available_slots(
            vehicle_type
        )


        print(
            f"\nAvailable "
            f"{vehicle_type.value} slots:"
        )


        if not slots:

            print(
                "No slots available."
            )

            return slots


        for slot in slots:

            print(
                f"  {slot.slot_id}"
            )

        return slots


    # ========================================================
    # DISPLAY OCCUPANCY
    # ========================================================

    def display_occupancy(self):

        self.parking_lot.display_occupancy()


# ============================================================
# MAIN / DRIVER PROGRAM
# ============================================================

def main():

    print("\n")
    print("==========================================")
    print("      MULTI-FLOOR PARKING LOT SYSTEM")
    print("==========================================")

    parking_lot = build_parking_lot()
    allocation_strategy = FirstAvailableSlotStrategy()
    fee_strategy = HourlyFeeStrategy()
    service = ParkingService(parking_lot, allocation_strategy, fee_strategy)

    while True:
        print("\n1. Park vehicle")
        print("2. Unpark vehicle")
        print("3. View available slots")
        print("4. Display occupancy")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            license_plate = input("Enter license plate: ").strip()
            vehicle_type_input = input("Enter vehicle type (bike/car/truck): ").strip()

            try:
                vehicle_type = parse_vehicle_type(vehicle_type_input)
                vehicle = VehicleFactory.create_vehicle(license_plate, vehicle_type)
                service.park_vehicle(vehicle)
            except ValueError as exc:
                print(f"ERROR: {exc}")

        elif choice == "2":
            ticket_id = input("Enter ticket ID: ").strip()
            service.unpark_vehicle(ticket_id)

        elif choice == "3":
            vehicle_type_input = input("Enter vehicle type (bike/car/truck): ").strip()

            try:
                vehicle_type = parse_vehicle_type(vehicle_type_input)
                service.get_available_slots(vehicle_type)
            except ValueError as exc:
                print(f"ERROR: {exc}")

        elif choice == "4":
            service.display_occupancy()

        elif choice == "5":
            print("Thank you for using the parking system.")
            break

        else:
            print("Invalid option. Please select 1 to 5.")


if __name__ == "__main__":
    main()