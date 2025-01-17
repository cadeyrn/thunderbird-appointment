"""Module: models

Definitions of database tables and their relationships.
"""
import datetime
import enum
import os
import uuid
import zoneinfo

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum, Boolean, JSON, Date, Time
from sqlalchemy_utils import StringEncryptedType, ChoiceType, UUIDType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from sqlalchemy.orm import relationship, as_declarative, declared_attr, Mapped
from sqlalchemy.sql import func


def secret():
    return os.getenv("DB_SECRET")


def random_slug():
    return "".join(str(uuid.uuid4()).split("-"))


class SubscriberLevel(enum.Enum):
    basic = 1  # basic tier
    plus = 2  # advanced tier
    pro = 3  # pro tier
    admin = 99  # unlimited tier


class AppointmentStatus(enum.Enum):
    draft = 1  # appointment was created but not published yet
    opened = 2  # appointment is published and waiting for attendees
    closed = 3  # appointment is published and fulfilled or manually closed for attendees


class BookingStatus(enum.Enum):
    none = 1  # slot status doesn't matter, because the parent object holds the state
    requested = 2  # booking slot was requested
    booked = 3  # booking slot was assigned


class LocationType(enum.Enum):
    inperson = 1  # appointment is held in person
    online = 2  # appointment is held online


class CalendarProvider(enum.Enum):
    caldav = 1  # calendar provider serves via CalDAV
    google = 2  # calendar provider is Google via its own Rest API


# Use ISO 8601 format to specify day of week
class DayOfWeek(enum.Enum):
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6
    Sunday = 7


class ExternalConnectionType(enum.Enum):
    zoom = 1
    google = 2
    fxa = 3


class MeetingLinkProviderType(enum.StrEnum):
    none = 'none'
    zoom = 'zoom'
    google_meet = 'google_meet'


class InviteStatus(enum.Enum):
    active = 1  # The code is still valid. It may be already used or is still to be used
    revoked = 2  # The code is no longer valid and cannot be used for sign up anymore


@as_declarative()
class Base:
    """Base model, contains anything we want to be on every model."""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def touch(self):
        """Updates the time_updated field with the current datetime. This function does not save the model!"""
        self.time_updated = datetime.datetime.now()

    time_created = Column(DateTime, server_default=func.now(), default=func.now(), index=True)
    time_updated = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now(), index=True)


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), unique=True, index=True)
    # Encrypted (here) and hashed (by the associated hashing functions in routes/auth)
    password = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=False)
    email = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), unique=True, index=True)
    name = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    level = Column(Enum(SubscriberLevel), default=SubscriberLevel.basic, index=True)
    timezone = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    avatar_url = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=2048), index=False)

    short_link_hash = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=False)

    # Only accept the times greater than the one specified in the `iat` claim of the jwt token
    minimum_valid_iat_time = Column('minimum_valid_iat_time', StringEncryptedType(DateTime, secret, AesEngine, "pkcs5", length=255))

    calendars = relationship("Calendar", cascade="all,delete", back_populates="owner")
    slots = relationship("Slot", cascade="all,delete", back_populates="subscriber")
    external_connections = relationship("ExternalConnections", cascade="all,delete", back_populates="owner")
    invite: Mapped["Invite"] = relationship("Invite", back_populates="subscriber", uselist=False)

    def get_external_connection(self, type: ExternalConnectionType) -> 'ExternalConnections':
        """Retrieves the first found external connection by type or returns None if not found"""
        return next(filter(lambda ec: ec.type == type, self.external_connections), None)


class Calendar(Base):
    __tablename__ = "calendars"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("subscribers.id"))
    provider = Column(Enum(CalendarProvider), default=CalendarProvider.caldav)
    title = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    color = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=32), index=True)
    url = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=2048), index=False)
    user = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    password = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255))
    connected = Column(Boolean, index=True, default=False)
    connected_at = Column(DateTime)

    owner: Subscriber = relationship("Subscriber", back_populates="calendars")
    appointments: list["Appointment"] = relationship("Appointment", cascade="all,delete", back_populates="calendar")
    schedules: list["Schedule"] = relationship("Schedule", cascade="all,delete", back_populates="calendar")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUIDType(native=False), default=uuid.uuid4(), index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"))
    duration = Column(Integer)
    title = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255))
    location_type = Column(Enum(LocationType), default=LocationType.inperson)
    location_suggestions = Column(String(255))
    location_selected = Column(Integer)
    location_name = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255))
    location_url = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=2048))
    location_phone = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255))
    details = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255))
    slug = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), unique=True, index=True)
    keep_open = Column(Boolean)
    status: AppointmentStatus = Column(Enum(AppointmentStatus), default=AppointmentStatus.draft)

    # What (if any) meeting link will we generate once the meeting is booked
    meeting_link_provider = Column(StringEncryptedType(ChoiceType(MeetingLinkProviderType), secret, AesEngine, "pkcs5", length=255), default=MeetingLinkProviderType.none, index=False)

    calendar = relationship("Calendar", back_populates="appointments")
    slots = relationship("Slot", cascade="all,delete", back_populates="appointment")


class Attendee(Base):
    __tablename__ = "attendees"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    name = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    timezone = Column(String(255), index=True)

    slots = relationship("Slot", cascade="all,delete", back_populates="attendee")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    attendee_id = Column(Integer, ForeignKey("attendees.id"))
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"))
    time_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    start = Column(DateTime)
    duration = Column(Integer)

    # provider specific id we can use to query against their service
    meeting_link_id = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=1024), index=False)
    # meeting link override for a appointment or schedule's location url
    meeting_link_url = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=2048))

    # columns for availability bookings
    booking_tkn = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=512), index=False)
    booking_expires_at = Column(DateTime)
    booking_status = Column(Enum(BookingStatus), default=BookingStatus.none)

    appointment: Appointment = relationship("Appointment", back_populates="slots")
    schedule: 'Schedule' = relationship("Schedule", back_populates="slots")

    attendee: Attendee = relationship("Attendee", cascade="all,delete", back_populates="slots")
    subscriber: Subscriber = relationship("Subscriber", back_populates="slots")


class Schedule(Base):
    __tablename__ = "schedules"

    id: int = Column(Integer, primary_key=True, index=True)
    calendar_id: int = Column(Integer, ForeignKey("calendars.id"))
    active: bool = Column(Boolean, index=True, default=True)
    name: str = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    location_type: LocationType = Column(Enum(LocationType), default=LocationType.inperson)
    location_url: str = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=2048))
    details: str = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255))
    start_date: datetime.date = Column(StringEncryptedType(Date, secret, AesEngine, "pkcs5", length=255), index=True)
    end_date: datetime.date = Column(StringEncryptedType(Date, secret, AesEngine, "pkcs5", length=255), index=True)
    start_time: datetime.time = Column(StringEncryptedType(Time, secret, AesEngine, "pkcs5", length=255), index=True)
    end_time: datetime.time = Column(StringEncryptedType(Time, secret, AesEngine, "pkcs5", length=255), index=True)
    earliest_booking: int = Column(Integer, default=1440)  # in minutes, defaults to 24 hours
    farthest_booking: int = Column(Integer, default=20160)  # in minutes, defaults to 2 weeks
    weekdays: str | dict = Column(JSON, default="[1,2,3,4,5]")  # list of ISO weekdays, Mo-Su => 1-7
    slot_duration: int = Column(Integer, default=30)  # defaults to 30 minutes

    # What (if any) meeting link will we generate once the meeting is booked
    meeting_link_provider: MeetingLinkProviderType = Column(StringEncryptedType(ChoiceType(MeetingLinkProviderType), secret, AesEngine, "pkcs5", length=255), default=MeetingLinkProviderType.none, index=False)

    calendar: Calendar = relationship("Calendar", back_populates="schedules")
    availabilities: list["Availability"] = relationship("Availability", cascade="all,delete", back_populates="schedule")
    slots: list[Slot] = relationship("Slot", cascade="all,delete", back_populates="schedule")

    @property
    def start_time_local(self) -> datetime.time:
        """Start Time in the Schedule's Calendar's Owner's timezone"""
        time_of_save = self.time_updated.replace(hour=self.start_time.hour, minute=self.start_time.minute, second=0, tzinfo=datetime.timezone.utc)
        return time_of_save.astimezone(zoneinfo.ZoneInfo(self.calendar.owner.timezone)).time()

    @property
    def end_time_local(self) -> datetime.time:
        """End Time in the Schedule's Calendar's Owner's timezone"""
        time_of_save = self.time_updated.replace(hour=self.end_time.hour, minute=self.end_time.minute, second=0, tzinfo=datetime.timezone.utc)
        return time_of_save.astimezone(zoneinfo.ZoneInfo(self.calendar.owner.timezone)).time()


class Availability(Base):
    """This table will be used as soon as the application provides custom availability
       in addition to the general availability
    """

    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    day_of_week = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    start_time = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    end_time = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    # Can't book if it's less than X minutes before start time:
    min_time_before_meeting = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    slot_duration = Column(Integer)  # Size of the Slot that can be booked.

    schedule = relationship("Schedule", back_populates="availabilities")


class ExternalConnections(Base):
    """This table holds all external service connections to a subscriber."""
    __tablename__ = "external_connections"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("subscribers.id"))
    name = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=False)
    type = Column(Enum(ExternalConnectionType), index=True)
    type_id = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=True)
    token = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=2048), index=False)
    owner = relationship("Subscriber", back_populates="external_connections")


class Invite(Base):
    """This table holds all invite codes for code based sign-ups."""
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"))
    code = Column(StringEncryptedType(String, secret, AesEngine, "pkcs5", length=255), index=False)
    status = Column(Enum(InviteStatus), index=True)

    subscriber: Mapped["Subscriber"] = relationship("Subscriber", back_populates="invite", single_parent=True)

    @property
    def is_used(self) -> bool:
        """True if the invite code is assigned to a subscriber"""
        return self.subscriber_id is not None

    @property
    def is_revoked(self) -> bool:
        """True if the invite code is revoked"""
        return self.status == InviteStatus.revoked

    @property
    def is_available(self) -> bool:
        """True if the invite code is not assigned nor revoked"""
        return self.subscriber_id is None and self.status == InviteStatus.active
