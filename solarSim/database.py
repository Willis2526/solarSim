""" Database handler """
import logging
import sqlite3

logger = logging.getLogger(__name__)


class Database:
    """ Database handler class """

    def __init__(self, file_name="database.db"):
        """ Setup """
        self.file_name = file_name
        self.db = None
        self.conn = None

        # Initialize the connection
        self.create_connection()

    def dict_factory(self, cursor, row):
        """ Adapt sqlite row_factory to return a dict result """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0].lower()] = row[idx]
        return d

    def init_database(self):
        """ See if database exists. If not, create a new one """
        try:
            self.conn.execute("select * from devices").fetchall()
        except Exception:
            logger.info("Database does not exist. Creating database..")
            self.create_database()

    def create_database(self):
        """ Create database """
        try:
            self.conn.executescript(
                """
                -- Create tables
                CREATE TABLE "deviceGroups" (
                    "id"	INTEGER NOT NULL UNIQUE,
                    "name"	TEXT NOT NULL UNIQUE,
                    PRIMARY KEY("id" AUTOINCREMENT)
                );
                CREATE TABLE "devices" (
                    "id"	INTEGER NOT NULL UNIQUE,
                    "groupId"	INTEGER NOT NULL,
                    "name"	INTEGER NOT NULL UNIQUE,
                    FOREIGN KEY("groupId") REFERENCES "deviceGroups"("id"),
                    PRIMARY KEY("id" AUTOINCREMENT)
                );
                CREATE TABLE "deviceInputs" (
                    "id"	INTEGER NOT NULL UNIQUE,
                    "deviceId"	INTEGER NOT NULL,
                    "name"	TEXT NOT NULL UNIQUE,
                    PRIMARY KEY("id" AUTOINCREMENT),
                    FOREIGN KEY("deviceId") REFERENCES "devices"("id")
                );

                -- Create Indexes
                CREATE INDEX "UniqDeviceGroup" ON "deviceGroups" (
                    "name"	ASC
                );
                CREATE INDEX "UniqDevice" ON "devices" (
                    "name"	ASC
                );
                CREATE INDEX "UniqdeviceInputs" ON "deviceInputs" (
                    "name"	ASC
                );
                """
            )
            logger.info("Database successfully created")
        except Exception as e:
            logger.error("Failed to create database. %s.", e)

    def createDefaultData(self):
        """ Create the default data """
        deviceGroups = [
            {"name": "inverters"},
            {"name": "feederBreakers"},
            {"name": "transformers"},
            {"name": "mainBreakers"},
            {"name": "checkMeters"}
        ]
        for group in deviceGroups:
            self.upsertDeviceGroups(group)

        devices = [
            {
                "name": "inverter1",
                "groupId": self.getDeviceGroupId("inverters")
            },
            {
                "name": "inverter2",
                "groupId": self.getDeviceGroupId("inverters")
            },
            {
                "name": "inverter3",
                "groupId": self.getDeviceGroupId("inverters")
            },
            {
                "name": "inverter4",
                "groupId": self.getDeviceGroupId("inverters")
            },
            {
                "name": "feeder1Breaker",
                "groupId": self.getDeviceGroupId("feederBreakers")
            },
            {
                "name": "feeder2Breaker",
                "groupId": self.getDeviceGroupId("feederBreakers")
            },
            {
                "name": "transformer1",
                "groupId": self.getDeviceGroupId("transformers")
            },
            {
                "name": "mainBreaker1",
                "groupId": self.getDeviceGroupId("mainBreakers")
            },
            {
                "name": "checkMeter1",
                "groupId": self.getDeviceGroupId("checkMeters")
            },
        ]

        for device in devices:
            self.upsertDevices(device)

        deviceInputs = [
            {
                "name": "inverter1",
                "deviceId": self.getDeviceId("feeder1Breaker")
            },
            {
                "name": "inverter2",
                "deviceId": self.getDeviceId("feeder1Breaker")
            },
            {
                "name": "inverter3",
                "deviceId": self.getDeviceId("feeder2Breaker")
            },
            {
                "name": "inverter4",
                "deviceId": self.getDeviceId("feeder2Breaker")
            },
            {
                "name": "feeder1Breaker",
                "deviceId": self.getDeviceId("mainBreaker1")
            },
            {
                "name": "feeder2Breaker",
                "deviceId": self.getDeviceId("mainBreaker1")
            },
            {
                "name": "feeder1Breaker",
                "deviceId": self.getDeviceId("transformer1")
            },
            {
                "name": "feeder2Breaker",
                "deviceId": self.getDeviceId("transformer1")
            },
            {
                "name": "transformer1",
                "deviceId": self.getDeviceId("mainBreaker1")
            },
        ]

        for input in deviceInputs:
            self.upsertDeviceInputs(input)

    def create_connection(self):
        """ Create sqlite connection """
        try:
            self.db = sqlite3.connect(
                self.file_name,
                detect_types=sqlite3.PARSE_DECLTYPES,
                isolation_level=None,
                check_same_thread=False,
            )
            self.db.row_factory = self.dict_factory
            self.conn = self.db.cursor()
            self.init_database()
            logger.info("Sqlite connection opened")
        except Exception as e:
            logger.error(e)

    def close_connection(self):
        """ Close sqlite connection """
        self.conn.close()
        logger.info("Sqlite connection closed")

    def read(self, table, name=None):
        """ Read from a table """
        # Check if a connection exists
        if not self.conn:
            self.create_connection()
        try:
            if name:
                result = self.conn.execute(
                    "SELECT * FROM ? WHERE name = ?", (table, name,)
                ).fetchone()
            else:
                result = self.conn.execute(
                    "SELECT * from ?", (table,)
                ).fetchall()
        except Exception as e:
            result = None
            logger.info("Failed to read from devices table. %s.", e)

        return result

    def getDeviceGroupId(self, groupName):
        """ Get an Id of a device group """
        groupId = self.conn.execute(
            "SELECT id FROM deviceGroups WHERE name = ?", (groupName,)
        ).fetchone()["id"]

        return str(groupId)

    def getDeviceId(self, deviceName):
        """ Get an Id of a device """
        deviceId = self.conn.execute(
            "SELECT id FROM devices WHERE name = ?", (deviceName,)
        ).fetchone()["id"]

        return str(deviceId)

    def upsertDeviceGroups(self, data):
        """ Upsert the device groups """
        # Check if a connection exists
        if not self.conn:
            self.create_connection()

        self.conn.execute(
            """
            INSERT INTO deviceGroups (name)
            VALUES(?)
            ON CONFLICT(name)
            DO UPDATE SET name=?;
            """,
            (data["name"], data["name"]),
        )

    def upsertDevices(self, data):
        """ Upsert the devices """
        # Check if a connection exists
        if not self.conn:
            self.create_connection()

        self.conn.execute(
            """
            INSERT INTO devices (name, groupId)
            VALUES(?, ?)
            ON CONFLICT(name)
            DO UPDATE SET name=?, groupId=?;
            """,
            (
                data["name"],
                data["groupId"],
                data["name"],
                data["groupId"]
            ),
        )

    def upsertDeviceInputs(self, data):
        """ Upsert the device inputs """
        # Check if a connection exists
        if not self.conn:
            self.create_connection()

        self.conn.execute(
            """
            INSERT INTO deviceInputs (name, deviceId)
            VALUES(?, ?)
            ON CONFLICT(id)
            DO UPDATE SET name=?, deviceId=?;
            """,
            (
                data["name"],
                data["deviceId"],
                data["name"],
                data["deviceId"]
            ),
        )



    def upsert(self, table, data):
        """ Insert or update data in devices table """
        # Check if a connection exists
        if not self.conn:
            self.create_connection()

        # Dynamically create values and column names from data
        columns = []
        values = []
        updates = []
        for d in data:
            columns.append(d)
            updates.append("{}=?".format(d))
            values.append(data[d])

        columns = ",".join(columns) if len(columns) > 1 else columns[0]
        updates = ",".join(updates) if len(updates) > 1 else updates[0]
        values = ",".join(values) if len(values) > 1 else values[0]

        sql = """
        INSERT INTO {table} ({columns})
        VALUES(?)
        ON CONFLICT(name)
        DO UPDATE SET {updates};
        """.format(
            table=table,
            columns=columns,
            updates=updates
        )

        self.conn.execute(sql, (values, values),)


if __name__ == "__main__":
    db = Database()
    db.createDefaultData()