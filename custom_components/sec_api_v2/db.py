import logging
import os
import re
import sqlite3

_LOGGER = logging.getLogger(__name__)

DB_PATH = None


def set_db_path(hass):
    """Set the database path based on the Home Assistant configuration directory."""
    global DB_PATH
    DB_PATH = hass.config.path("sec_contracts.db")


def initialize_db():
    """Initialize the contracts database and create tables if not exists."""

    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL,
            energy_type TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            segment TEXT NOT NULL,
            supplier TEXT NOT NULL,
            contract_name TEXT NOT NULL,
            price_component TEXT NOT NULL,
            month TEXT NULL,
            year TEXT NULL,
            sensor_id TEXT NULL,
            UNIQUE(energy_type, contract_type, segment, supplier, contract_name, price_component, month, year)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS top_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL,
            energy_type TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            segment TEXT NOT NULL,
            supplier TEXT NOT NULL,
            contract_name TEXT NOT NULL,
            price_component TEXT NOT NULL,
            month TEXT NULL,
            year TEXT NULL,
            ranking TEXT NOT NULL,
            UNIQUE(ranking)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT NOT NULL,
            original_sensor_id TEXT NOT NULL,
            custom_sensor_name TEXT NOT NULL,
            UNIQUE(custom_sensor_name)
        )
    """)

    conn.commit()
    conn.close()


def add_contract(
    entry_id,
    energy_type,
    contract_type,
    segment,
    supplier,
    contract_name,
    price_component,
    month=None,
    year=None,
):
    """Add a new contract to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO contracts (entry_id, energy_type, contract_type, segment, supplier, contract_name, price_component, month, year, sensor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entry_id,
                energy_type,
                contract_type,
                segment,
                supplier,
                contract_name,
                price_component,
                month if month is not None else "NULL",
                year if year is not None else "NULL",
                "NULL",
            ),
        )

        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()


def add_custom_sensor(entry_id, original_sensor_id, custom_sensor_name):
    """Insert or update a custom sensor mapping in the database based on custom_sensor_name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE custom_sensors
        SET entry_id = ?, original_sensor_id = ?
        WHERE custom_sensor_name = ?
    """,
        (entry_id, original_sensor_id, custom_sensor_name),
    )

    if cursor.rowcount == 0:
        cursor.execute(
            """
            INSERT INTO custom_sensors (entry_id, original_sensor_id, custom_sensor_name)
            VALUES (?, ?, ?)
        """,
            (entry_id, original_sensor_id, custom_sensor_name),
        )

    conn.commit()
    conn.close()


def get_contracts(entry_id):
    """Retrieve contracts for a specific config entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM contracts WHERE entry_id=?", (entry_id,))
    contracts = cursor.fetchall()

    conn.close()
    return contracts


def get_top_contracts(entry_id):
    """Retrieve top contracts for a specific config entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM top_contracts WHERE entry_id=?", (entry_id,))
    contracts = cursor.fetchall()

    conn.close()
    return contracts


def get_custom_sensors(entry_id):
    """Retrieve all custom sensor mappings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM custom_sensors WHERE entry_id=?", (entry_id,))
    sensors = cursor.fetchall()

    conn.close()
    return sensors


def update_sensor_id(
    sensor_id,
    energy_type,
    contract_type,
    segment,
    supplier,
    contract_name,
    price_component,
    month=None,
    year=None,
):
    """Update sensor id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    clean_sensor_id = strip_suffix(sensor_id)

    cursor.execute(
        """
        UPDATE contracts
        SET sensor_id=?
        WHERE energy_type=? AND contract_type=? AND segment=? AND supplier=? AND contract_name=? AND price_component=? AND month=? AND year=?
    """,
        (
            clean_sensor_id,
            energy_type,
            contract_type,
            segment,
            supplier,
            contract_name,
            price_component,
            month if month is not None else "NULL",
            year if year is not None else "NULL",
        ),
    )

    conn.commit()
    conn.close()


def remove_all_except_entry_id(entry_id):
    """Remove all entries from the contracts table except those with a specific entry_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM contracts
        WHERE entry_id != ?
        """,
        (entry_id,),
    )

    cursor.execute(
        """
        DELETE FROM custom_sensors
        WHERE entry_id != ?
        """,
        (entry_id,),
    )

    conn.commit()
    conn.close()


def remove_contract(sensor_id):
    """Remove contract and related custom sensors by given contract id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM contracts
        WHERE sensor_id = ?
        """,
        (sensor_id,),
    )

    cursor.execute(  # Also remove related custom sensors
        """
        DELETE FROM custom_sensors
        WHERE original_sensor_id = ?
        """,
        (sensor_id,),
    )

    conn.commit()
    conn.close()


def remove_custom_sensor(sensor_name):
    """Unregister custom sensor alias."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM custom_sensors
        WHERE custom_sensor_name = ?
        """,
        (sensor_name,),
    )

    conn.commit()
    conn.close()


def empty_top_contracts():
    """Empty top contracts table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM top_contracts;
        """
    )

    conn.commit()
    conn.close()


def add_top_contract(
    ranking,
    entry_id,
    energy_type,
    contract_type,
    segment,
    supplier,
    contract_name,
    price_component,
    month=None,
    year=None,
):
    """Insert or update a row in the top_contracts table based on the ranking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE top_contracts
        SET entry_id = ?, energy_type = ?, contract_type = ?, segment = ?, supplier = ?,
            contract_name = ?, price_component = ?, month = ?, year = ?
        WHERE ranking = ?
        """,
        (
            entry_id,
            energy_type,
            contract_type,
            segment,
            supplier,
            contract_name,
            price_component,
            month if month is not None else "NULL",
            year if year is not None else "NULL",
            ranking,
        ),
    )

    if cursor.rowcount == 0:
        cursor.execute(
            """
            INSERT INTO top_contracts (entry_id, energy_type, contract_type, segment, supplier,
                                        contract_name, price_component, month, year, ranking)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                energy_type,
                contract_type,
                segment,
                supplier,
                contract_name,
                price_component,
                month if month is not None else "NULL",
                year if year is not None else "NULL",
                ranking,
            ),
        )

    conn.commit()
    conn.close()


def strip_suffix(sensor_id):
    """Remove numeric suffix like _2, _3 from the sensor_id."""
    return re.sub(r"_\d+$", "", sensor_id)
