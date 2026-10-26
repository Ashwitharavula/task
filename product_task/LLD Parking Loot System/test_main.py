from datetime import datetime, timedelta

import main


def make_service():
    parking_lot = main.build_parking_lot()
    service = main.ParkingService(
        parking_lot,
        main.FirstAvailableSlotStrategy(),
        main.HourlyFeeStrategy(),
    )
    return parking_lot, service


def make_vehicle(license_plate="TEST-1", vehicle_type=main.VehicleType.CAR):
    return main.VehicleFactory.create_vehicle(license_plate, vehicle_type)


def assert_raises(exception_type, operation, *args):
    try:
        operation(*args)
    except exception_type:
        return
    raise AssertionError(f"Expected {exception_type.__name__}")


def test_parse_vehicle_type():
    assert main.parse_vehicle_type("car") == main.VehicleType.CAR
    assert main.parse_vehicle_type("BIKE") == main.VehicleType.BIKE


def test_build_parking_lot_has_slots():
    lot = main.build_parking_lot()
    assert len(lot.floors) == 2
    assert len(lot.floors[0].slots) > 0


def test_duplicate_vehicle_is_rejected_until_it_exits():
    _, service = make_service()
    ticket = service.park_vehicle(make_vehicle())

    assert ticket is not None
    assert service.park_vehicle(make_vehicle("test-1")) is None

    service.unpark_vehicle(ticket.ticket_id)
    next_ticket = service.park_vehicle(make_vehicle())

    assert next_ticket is not None
    assert next_ticket.ticket_id != ticket.ticket_id


def test_invalid_and_reused_ticket_ids_do_not_exit_a_vehicle():
    _, service = make_service()
    ticket = service.park_vehicle(make_vehicle())

    assert service.unpark_vehicle(None) is None
    service.unpark_vehicle(ticket.ticket_id)
    service.unpark_vehicle(ticket.ticket_id)

    assert ticket.exit_time is not None
    assert ticket.slot.is_available()


def test_exit_releases_the_ticket_vehicle_slot():
    _, service = make_service()
    ticket = service.park_vehicle(make_vehicle())
    original_slot = ticket.slot

    service.unpark_vehicle(ticket.ticket_id)

    assert original_slot.vehicle is None
    assert original_slot.is_available()


def test_slot_rejects_unsupported_or_second_vehicle():
    slot = main.ParkingSlot("B1", main.VehicleType.BIKE)
    car = make_vehicle()

    assert_raises(ValueError, slot.assign_vehicle, car)

    bike = make_vehicle("BIKE-1", main.VehicleType.BIKE)
    slot.assign_vehicle(bike)
    assert_raises(
        ValueError,
        slot.assign_vehicle,
        make_vehicle("BIKE-2", main.VehicleType.BIKE),
    )

    assert slot.vehicle is bike


def test_failed_parking_does_not_create_a_ticket():
    _, service = make_service()
    first_ticket = service.park_vehicle(
        make_vehicle("TRUCK-1", main.VehicleType.TRUCK)
    )

    assert service.park_vehicle(
        make_vehicle("TRUCK-2", main.VehicleType.TRUCK)
    ) is None
    assert list(service.tickets) == [first_ticket.ticket_id]
    assert service.ticket_counter == 2


def test_available_slots_update_after_parking_and_exit():
    _, service = make_service()
    initial_slots = service.get_available_slots(main.VehicleType.CAR)
    ticket = service.park_vehicle(make_vehicle())
    after_parking = service.get_available_slots(main.VehicleType.CAR)

    service.unpark_vehicle(ticket.ticket_id)
    after_exit = service.get_available_slots(main.VehicleType.CAR)

    assert len(initial_slots) == 2
    assert len(after_parking) == 1
    assert len(after_exit) == 2


def test_fee_uses_minimum_one_hour_and_rounds_up():
    fee_strategy = main.HourlyFeeStrategy()
    ticket = main.Ticket("T1", make_vehicle(), main.ParkingSlot("C1", main.VehicleType.CAR))
    ticket.entry_time = datetime.now() - timedelta(minutes=10)

    assert fee_strategy.calculate_fee(ticket) == 40

    ticket.entry_time = datetime.now() - timedelta(minutes=61)
    assert fee_strategy.calculate_fee(ticket) == 80


def test_occupancy_display_matches_parked_and_exited_state(capsys):
    _, service = make_service()
    ticket = service.park_vehicle(make_vehicle("CAR-9"))

    service.display_occupancy()
    assert "OCCUPIED by CAR-9" in capsys.readouterr().out

    service.unpark_vehicle(ticket.ticket_id)
    service.display_occupancy()
    assert "F1-C1 (CAR) -> FREE" in capsys.readouterr().out


def test_invalid_vehicle_type_is_handled_safely():
    assert_raises(
        ValueError,
        main.VehicleFactory.create_vehicle,
        "BAD-1",
        "BUS",
    )

    _, service = make_service()
    assert service.get_available_slots("BUS") == []


def test_invalid_menu_choice_is_handled_safely(monkeypatch, capsys):
    choices = iter(["not-a-choice", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(choices))

    main.main()

    assert "Invalid option" in capsys.readouterr().out


if __name__ == "__main__":
    import pytest
    pytest.main(["-v", __file__])
